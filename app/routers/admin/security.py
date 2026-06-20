from fastapi import APIRouter, Depends, HTTPException
from psycopg.rows import dict_row

from app.core.security import require_admin, decode_token, generate_api_key
from app.database.connection import get_db_connection, get_redis_client
from app.schemas.models import APIKeyCreate, APIKeySummaryAdmin, ActiveSession, SecurityOverview
from app.utils.responses import success

api_router = APIRouter(prefix="/security", tags=["admin-security"])


def _mask_key(key: str) -> str:
    return f"PYTOGO_SK_{'*' * 28}{key[-4:]}"


@api_router.get("/overview")
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

    data = SecurityOverview(
        total_api_keys=total_api_keys,
        active_sessions=len(active_sessions),
        cached_api_keys=len(cached_keys),
        active_carts=len(active_carts),
    )
    return success(data)


@api_router.post("/api-keys", status_code=201)
async def create_api_key(
    payload: APIKeyCreate,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    key_value = generate_api_key()
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO api_keys (name, key_value, event_id)
            VALUES (%s, %s, %s)
            RETURNING id, name, key_value, event_id, created_at
            """,
            (payload.name, key_value, payload.event_id),
        )
        row = await cur.fetchone()
    return success({"id": row["id"], "name": row["name"], "key_value": row["key_value"],
                    "event_id": row["event_id"], "created_at": row["created_at"]}, code=201)


@api_router.get("/api-keys")
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
        result.append(APIKeySummaryAdmin(
            id=row["id"],
            name=row["name"],
            key_masked=_mask_key(row["key_value"]),
            event_id=row["event_id"],
            event_code=row["event_code"],
            created_at=row["created_at"],
            is_cached=bool(cached),
        ))
    return success(result)


@api_router.get("/sessions")
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
    return success(sessions)

@api_router.get("/api-keys/{key_id}")
async def get_api_key_details(
    key_id: str,
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
            WHERE k.id = %s
            """,
            (key_id,),
        )
        row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="API key not found")
        cached = await redis.exists(f"PYTOGO_API_KEY:{row['key_value']}")
        result = APIKeySummaryAdmin(
            id=row["id"],
            name=row["name"],
            key_masked=_mask_key(row["key_value"]),
            event_id=row["event_id"],
            event_code=row["event_code"],
            created_at=row["created_at"],
            is_cached=bool(cached),
        )
    return success(result)

@api_router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    db=Depends(get_db_connection),
    redis=Depends(get_redis_client),
    _=Depends(require_admin),
):
    async with db.cursor() as cur:
        await cur.execute("DELETE FROM api_keys WHERE id = %s", (key_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="API key not found")
    # Remove from Redis cache if exists
    await redis.delete(f"PYTOGO_API_KEY:{key_id}")
    return success({"message": "API key deleted successfully"})