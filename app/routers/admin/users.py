from fastapi import APIRouter, Depends, Query
from psycopg.rows import dict_row

from app.core.security import require_admin
from app.database.connection import get_db_connection
from app.schemas.models import UserSummary, UsersDashboardOverview
from app.utils.responses import success
from app.utils.pagination import paginate

api_router = APIRouter(prefix="/users", tags=["admin-users"])


@api_router.get("/overview")
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

    data = UsersDashboardOverview(
        total_users=total,
        active_users=active,
        inactive_users=inactive,
        new_last_7_days=new_last_7,
        by_role=by_role,
    )
    return success(data)


@api_router.get("/inactive")
async def list_inactive_users(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    rows, total = await paginate(
        db,
        "SELECT * FROM users WHERE is_active = false ORDER BY created_at DESC",
        (),
        page, per_page,
    )
    return success([UserSummary(**r) for r in rows], total=total, page=page, per_page=per_page)


@api_router.get("/new")
async def list_new_users(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    rows, total = await paginate(
        db,
        "SELECT * FROM users WHERE created_at >= NOW() - INTERVAL '7 days' ORDER BY created_at DESC",
        (),
        page, per_page,
    )
    return success([UserSummary(**r) for r in rows], total=total, page=page, per_page=per_page)


@api_router.get("/no-orders")
async def list_users_without_orders(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    rows, total = await paginate(
        db,
        """
        SELECT u.* FROM users u
        WHERE NOT EXISTS (
            SELECT 1 FROM shop_orders o WHERE o.user_id = u.id
        )
        ORDER BY u.created_at DESC
        """,
        (),
        page, per_page,
    )
    return success([UserSummary(**r) for r in rows], total=total, page=page, per_page=per_page)
