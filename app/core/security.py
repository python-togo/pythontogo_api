from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated, Callable
from app.database.connection import get_db_connection, get_redis_client
from app.database.orm import select
from json import dumps, loads
from app.schemas.models import (
    APIKeyResponse,
    APIKeyVerificationResponse,
    AuthenticatedUser,
    TokenData,
    UserSummary,
    UserRole,
)
from app.core.settings import settings
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
from psycopg.rows import dict_row

security = HTTPBearer()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    """Build an access JWT.

    Expected keys in `data`:
      - sub          : user UUID (str)
      - email        : user email
      - role         : legacy UserRole enum value
      - is_admin     : bool — True if user has RBAC roles
      - permissions  : list[str] — e.g. ["users:read", "events:create"]
    """
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
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


def extract_token_payload(token: str) -> dict:
    """Public helper to inspect JWT claims without raising HTTP errors.

    Returns the decoded payload dict or an empty dict on failure.
    """
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except Exception:
        return {}


async def get_user_permissions_from_db(user_id: str, db) -> list[str]:
    """Fetch all permission names for a user via their assigned roles.

    Called at login/refresh time to embed permissions in the JWT.
    Not called on every authenticated request — JWT is the source of truth.
    """
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT DISTINCT p.name
            FROM user_roles ur
            JOIN role_permissions rp ON rp.role_id = ur.role_id
            JOIN permissions p ON p.id = rp.permission_id
            WHERE ur.user_id = %s
            ORDER BY p.name
            """,
            (user_id,),
        )
        rows = await cur.fetchall()
    return [row["name"] for row in rows]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db=Depends(get_db_connection),
) -> AuthenticatedUser:
    """Decode JWT, verify the user is still active, return AuthenticatedUser.

    Permissions and is_admin come directly from the JWT — no extra DB query.
    """
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    rows = await select(db, "users", filter={"id": user_id})
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    user = rows[0]
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )

    permissions: list[str] = payload.get("permissions", [])
    is_admin: bool = payload.get("is_admin", False)

    return AuthenticatedUser(
        **user,
        permissions=permissions,
        is_admin=is_admin,
    )


# ---------------------------------------------------------------------------
# Authorization helpers
# ---------------------------------------------------------------------------

async def require_admin(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> AuthenticatedUser:
    """Backward-compatible guard: user must be admin or staff (legacy role)."""
    if current_user.role not in (UserRole.ADMIN, UserRole.STAFF):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user


def require_permission(permission: str) -> Callable:
    """Dependency factory for granular permission checks.

    Usage::

        @router.post("/something")
        async def endpoint(_=Depends(require_permission("events:create"))):
            ...

    The check requires **both**:
      1. ``is_admin = True`` in the JWT  (user has at least one RBAC role)
      2. The requested permission is present in ``JWT.permissions``
    """
    async def _check(
        current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    ) -> AuthenticatedUser:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )
        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}",
            )
        return current_user

    return _check


# ---------------------------------------------------------------------------
# API key helpers
# ---------------------------------------------------------------------------

def generate_api_key():
    from nanoid import generate
    generated_key = generate(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        size=40,
    )
    return f"PYTOGO_SK_{generated_key}"


async def verify_api_key(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db=Depends(get_db_connection),
    redis=Depends(get_redis_client),
):
    api_key_value = credentials.credentials
    if not api_key_value.startswith("PYTOGO_SK_") or len(api_key_value) != 50:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
        )

    expected_api_key = await redis.get(f"PYTOGO_API_KEY:{credentials.credentials}")
    if not expected_api_key:
        expected_api_key = await select(
            db, "api_keys", filter={"key_value": credentials.credentials}
        )
        if not expected_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="API key not found"
            )
        expected_api_key = expected_api_key[0]
        api_key_data = {
            "name": expected_api_key["name"],
            "key_value": expected_api_key["key_value"],
        }
        await redis.set(
            f"PYTOGO_API_KEY:{credentials.credentials}", dumps(api_key_data), ex=3600
        )

    expected_api_key_data = (
        loads(expected_api_key)
        if isinstance(expected_api_key, bytes)
        else expected_api_key
    )
    if expected_api_key_data["key_value"] != credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )
    return APIKeyVerificationResponse(is_valid=True, message="API key is valid")
