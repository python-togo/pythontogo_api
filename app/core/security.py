from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPBasicCredentials
from typing import Annotated
from app.database.connection import get_db_connection, get_redis_client
from app.database.orm import select
from json import dumps, loads
from app.schemas.models import APIKeyResponse, APIKeyVerificationResponse
from app.core.settings import settings

security = HTTPBearer()


def generate_api_key():
    from nanoid import generate
    genrated_key = generate(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", size=40)

    api_key = f"PYTOGO_SK_{genrated_key}"
    return api_key


async def verify_api_key(request: Request, db=Depends(get_db_connection), redis=Depends(get_redis_client)):

    api_key_value = None

    if api_key_value is None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            api_key_value = auth_header[7:]

    if api_key_value is None:
        api_key_value = request.headers.get("X-API-Key")

    if not api_key_value or not api_key_value.startswith("PYTOGO_SK_") or len(api_key_value) != 50:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key format")
    expected_api_key = await redis.get(f"PYTOGO_API_KEY:{api_key_value}")
    if not expected_api_key:
        expected_api_key = await select(db, "api_keys", filter={"key_value": api_key_value})
        if not expected_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="API key not found")
        expected_api_key = expected_api_key[0]
        api_key_data = {
            "name": expected_api_key["name"],
            "key_value": expected_api_key["key_value"],
        }
        await redis.set(f"PYTOGO_API_KEY:{api_key_value}", dumps(api_key_data), ex=3600)

    expected_api_key_data = loads(expected_api_key) if isinstance(
        expected_api_key, bytes) else expected_api_key
    if expected_api_key_data["key_value"] != api_key_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return APIKeyVerificationResponse(is_valid=True, message="API key is valid")


async def require_admin_secret(request: Request):
    if not settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Admin secret not configured")
    admin_secret = request.headers.get("X-Admin-Secret")
    if admin_secret != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return True
