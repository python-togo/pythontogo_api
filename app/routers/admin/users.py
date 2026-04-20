from fastapi import APIRouter, Depends
from psycopg.rows import dict_row

from app.core.security import require_admin
from app.database.connection import get_db_connection
from app.schemas.models import UserSummary, UsersDashboardOverview

api_router = APIRouter(prefix="/users", tags=["admin-users"])


@api_router.get("/overview", response_model=UsersDashboardOverview)
async def get_users_overview(
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT COUNT(*) AS total FROM users")
        total = (await cur.fetchone())["total"]

        await cur.execute("SELECT COUNT(*) AS total FROM users WHERE is_active = true")
        active = (await cur.fetchone())["total"]

        await cur.execute("SELECT COUNT(*) AS total FROM users WHERE is_active = false")
        inactive = (await cur.fetchone())["total"]

        await cur.execute(
            "SELECT COUNT(*) AS total FROM users "
            "WHERE created_at >= NOW() - INTERVAL '7 days'"
        )
        new_last_7 = (await cur.fetchone())["total"]

        await cur.execute("SELECT role, COUNT(*) AS cnt FROM users GROUP BY role")
        role_rows = await cur.fetchall()

    by_role = {row["role"]: row["cnt"] for row in role_rows}

    return UsersDashboardOverview(
        total_users=total,
        active_users=active,
        inactive_users=inactive,
        new_last_7_days=new_last_7,
        by_role=by_role,
    )


@api_router.get("/inactive", response_model=list[UserSummary])
async def list_inactive_users(
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT * FROM users WHERE is_active = false ORDER BY created_at DESC"
        )
        rows = await cur.fetchall()
    return [UserSummary(**r) for r in rows]


@api_router.get("/new", response_model=list[UserSummary])
async def list_new_users(
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT * FROM users "
            "WHERE created_at >= NOW() - INTERVAL '7 days' "
            "ORDER BY created_at DESC"
        )
        rows = await cur.fetchall()
    return [UserSummary(**r) for r in rows]


@api_router.get("/no-orders", response_model=list[UserSummary])
async def list_users_without_orders(
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT u.* FROM users u
            WHERE NOT EXISTS (
                SELECT 1 FROM shop_orders o WHERE o.user_id = u.id
            )
            ORDER BY u.created_at DESC
            """
        )
        rows = await cur.fetchall()
    return [UserSummary(**r) for r in rows]
