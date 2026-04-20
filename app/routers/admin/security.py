from fastapi import APIRouter, Depends
from psycopg.rows import dict_row

from app.core.security import require_admin, decode_token
from app.database.connection import get_db_connection, get_redis_client
from app.schemas.models import APIKeySummaryAdmin, ActiveSession, SecurityOverview

api_router = APIRouter(prefix="/security", tags=["admin-security"])


def _mask_key(key: str) -> str:
    """Keep prefix + last 4 chars, hide the middle."""
    return f"PYTOGO_SK_{'*' * 28}{key[-4:]}"


@api_router.get("/overview", response_model=SecurityOverview)
async def get_security_overview(
    db=Depends(get_db_connection),
    redis=Depends(get_redis_client),
    _=Depends(require_admin),
):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT COUNT(*) AS total FROM api_keys")
        total_api_keys = (await cur.fetchone())["total"]

    cached_keys = await redis.keys("PYTOGO_API_KEY:*")
    active_sessions = await redis.keys("PYTOGO_REFRESH:*")
    active_carts = await redis.keys("PYTOGO_CART:*")

    return SecurityOverview(
        total_api_keys=total_api_keys,
        active_sessions=len(active_sessions),
        cached_api_keys=len(cached_keys),
        active_carts=len(active_carts),
    )


@api_router.get("/api-keys", response_model=list[APIKeySummaryAdmin])
async def list_api_keys(
    db=Depends(get_db_connection),
    redis=Depends(get_redis_client),
    _=Depends(require_admin),
):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT k.id, k.name, k.key_value, k.event_id, k.created_at,
                   e.code AS event_code
            FROM api_keys k
            LEFT JOIN events e ON e.id = k.event_id
            ORDER BY k.created_at DESC
            """
        )
        rows = await cur.fetchall()

    result = []
    for row in rows:
        cached = await redis.exists(f"PYTOGO_API_KEY:{row['key_value']}")
        result.append(
            APIKeySummaryAdmin(
                id=row["id"],
                name=row["name"],
                key_masked=_mask_key(row["key_value"]),
                event_id=row["event_id"],
                event_code=row["event_code"],
                created_at=row["created_at"],
                is_cached=bool(cached),
            )
        )
    return result


@api_router.get("/sessions", response_model=list[ActiveSession])
async def list_active_sessions(
    redis=Depends(get_redis_client),
    _=Depends(require_admin),
):
    keys = await redis.keys("PYTOGO_REFRESH:*")
    sessions = []
    for key in keys:
        ttl = await redis.ttl(key)
        if ttl <= 0:
            continue
        token = await redis.get(key)
        email = None
        user_id = key.decode().removeprefix("PYTOGO_REFRESH:")
        if token:
            try:
                payload = decode_token(token.decode())
                email = payload.get("email")
            except Exception:
                pass
        sessions.append(ActiveSession(user_id=user_id, email=email, expires_in_seconds=ttl))
    return sessions
