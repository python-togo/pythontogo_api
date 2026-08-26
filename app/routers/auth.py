from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.auth import (
    create_access_token,
    create_refresh_token,
    verify_password,
    hash_password,
    get_current_user,
    get_current_superuser,
    decode_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.database.connection import get_db_connection
from app.database.orm import select, insert, delete
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int


class TokenRefresh(BaseModel):
    refresh_token: str


class LoginRequest(BaseModel):
    email: str
    password: str


class MessageResponse(BaseModel):
    message: str


api_router = APIRouter(prefix="/auth", tags=["auth"])


@api_router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(payload: LoginRequest, db=Depends(get_db_connection)):
    users = await select(db, "users", filter={"email": payload.email})
    if not users:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    user = users[0]
    if not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.get("is_active", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    access_token = create_access_token(subject=user["id"])
    refresh_token = create_refresh_token(user_id=user["id"])

    now = datetime.now(timezone.utc)
    refresh_expires = now + timedelta(days=7)
    await insert(db, "refresh_tokens", {
        "user_id": user["id"],
        "token": refresh_token,
        "expires_at": refresh_expires.isoformat(),
        "revoked": False,
    })

    return Token(access_token=access_token, refresh_token=refresh_token, expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60)


@api_router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
async def refresh_token(payload: TokenRefresh, db=Depends(get_db_connection)):
    try:
        token_data = decode_token(payload.refresh_token)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if token_data.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = token_data.get("sub")
    stored = await select(db, "refresh_tokens", filter={"token": payload.refresh_token, "user_id": user_id, "revoked": False})
    if not stored:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found or revoked")

    token_row = stored[0]
    expires_at = token_row.get("expires_at")
    # La colonne est un TIMESTAMPTZ : psycopg renvoie deja un datetime.
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    if expires_at and expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    users = await select(db, "users", filter={"id": user_id})
    if not users or not users[0].get("is_active", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found or inactive")

    user = users[0]
    await delete(db, "refresh_tokens", filter={"token": payload.refresh_token})

    new_access = create_access_token(subject=user["id"])
    new_refresh = create_refresh_token(user_id=user["id"])
    now = datetime.now(timezone.utc)
    await insert(db, "refresh_tokens", {
        "user_id": user["id"],
        "token": new_refresh,
        "expires_at": (now + timedelta(days=7)).isoformat(),
        "revoked": False,
    })

    return Token(access_token=new_access, refresh_token=new_refresh, expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60)


@api_router.post("/logout", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def logout(payload: TokenRefresh, db=Depends(get_db_connection)):
    await delete(db, "refresh_tokens", filter={"token": payload.refresh_token})
    return MessageResponse(message="Logged out successfully")
