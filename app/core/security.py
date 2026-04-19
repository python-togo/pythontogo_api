from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
from app.database.connection import get_db_connection, get_redis_client
from app.database.orm import select
from json import dumps, loads
from app.schemas.models import APIKeyResponse, APIKeyVerificationResponse, TokenData, UserSummary
from app.core.settings import settings
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt

security = HTTPBearer()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload["type"] = "access"
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(days=7)
    payload["type"] = "refresh"
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db=Depends(get_db_connection),
) -> UserSummary:
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    rows = await select(db, "users", filter={"id": user_id})
    if not rows:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    user = rows[0]
    if not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return UserSummary(**user)


def generate_api_key():
    from nanoid import generate
    genrated_key = generate(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", size=40)

    api_key = f"PYTOGO_SK_{genrated_key}"
    return api_key


async def verify_api_key(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)], db=Depends(get_db_connection), redis=Depends(get_redis_client)):

    api_key_value = credentials.credentials
    if not api_key_value.startswith("PYTOGO_SK_") or len(api_key_value) != 50:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key format")
    expected_api_key = await redis.get(f"PYTOGO_API_KEY:{credentials.credentials}")
    if not expected_api_key:
        expected_api_key = await select(db, "api_keys", filter={"key_value": credentials.credentials})
        if not expected_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="API key not found")
        expected_api_key = expected_api_key[0]
        # Cache for 1 hour
        api_key_data = {
            "name": expected_api_key["name"],
            "key_value": expected_api_key["key_value"],
        }
        await redis.set(f"PYTOGO_API_KEY:{credentials.credentials}", dumps(api_key_data), ex=3600)

    expected_api_key_data = loads(expected_api_key) if isinstance(
        expected_api_key, bytes) else expected_api_key
    if expected_api_key_data["key_value"] != credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return APIKeyVerificationResponse(is_valid=True, message="API key is valid")
