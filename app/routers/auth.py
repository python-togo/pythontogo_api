from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Annotated
from app.database.connection import get_db_connection, get_redis_client
from app.database.orm import select, insert
from app.schemas.models import AuthenticatedUser, UserCreate, UserLogin, UserSummary
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    get_user_permissions_from_db,
)
from app.utils.responses import success

api_router = APIRouter(prefix="/auth", tags=["auth"])

_REFRESH_TTL = 7 * 24 * 3600


async def _build_token_data(user: dict, db) -> dict:
    user_id = str(user["id"])
    permissions = await get_user_permissions_from_db(user_id, db)
    return {
        "sub": user_id,
        "email": user["email"],
        "role": user["role"],
        "is_admin": len(permissions) > 0,
        "permissions": permissions,
    }


@api_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db=Depends(get_db_connection)):
    existing = await select(db, "users", filter={"email": payload.email})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    existing_username = await select(db, "users", filter={"username": payload.username})
    if existing_username:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    data = {
        "username": payload.username,
        "email": payload.email,
        "full_name": payload.full_name,
        "password_hash": hash_password(payload.password),
        "role": "member",
        "is_active": True,
    }
    await insert(db, "users", data)

    rows = await select(db, "users", filter={"email": payload.email})
    return success(UserSummary(**rows[0]), code=201)


@api_router.post("/login")
async def login(payload: UserLogin, db=Depends(get_db_connection), redis=Depends(get_redis_client)):
    rows = await select(db, "users", filter={"email": payload.email})
    if not rows or not verify_password(payload.password, rows[0]["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user = rows[0]
    if not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    token_data = await _build_token_data(user, db)
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": token_data["sub"], "email": token_data["email"]})

    await redis.set(f"PYTOGO_REFRESH:{user['id']}", refresh_token, ex=_REFRESH_TTL)

    return success({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    })


@api_router.post("/refresh")
async def refresh(refresh_token: str, db=Depends(get_db_connection), redis=Depends(get_redis_client)):
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    stored = await redis.get(f"PYTOGO_REFRESH:{user_id}")
    if not stored or stored.decode() != refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked or invalid")

    rows = await select(db, "users", filter={"id": user_id})
    if not rows or not rows[0]["is_active"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    user = rows[0]
    token_data = await _build_token_data(user, db)
    new_access = create_access_token(token_data)
    new_refresh = create_refresh_token({"sub": token_data["sub"], "email": token_data["email"]})

    await redis.set(f"PYTOGO_REFRESH:{user_id}", new_refresh, ex=_REFRESH_TTL)

    return success({
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    })


@api_router.post("/logout")
async def logout(current_user: Annotated[AuthenticatedUser, Depends(get_current_user)], redis=Depends(get_redis_client)):
    await redis.delete(f"PYTOGO_REFRESH:{current_user.id}")
    return success({"message": "Logged out successfully"})


@api_router.get("/me")
async def me(current_user: Annotated[AuthenticatedUser, Depends(get_current_user)]):
    return success(current_user)
