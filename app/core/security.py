from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPBasicCredentials
from typing import Annotated
from app.database.connection import get_db_connection, get_redis_client
from app.database.orm import select
from json import dumps, loads
from app.schemas.models import APIKeyResponse, APIKeyVerificationResponse

security = HTTPBearer()


def generate_api_key():
    from nanoid import generate
    genrated_key = generate(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", size=32)

    api_key = f"PYTOGO_SK_{genrated_key}"
    return api_key


async def verify_api_key(credentials: Annotated[HTTPBasicCredentials, Depends(security)], db=Depends(get_db_connection), redis=Depends(get_redis_client)):

    api_key_value = credentials.credentials
    if not api_key_value.startswith("PYTOGO_SK_") or len(api_key_value) != 42:
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
