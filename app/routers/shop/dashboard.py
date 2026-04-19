from fastapi import APIRouter, Depends
from psycopg.rows import dict_row
from decimal import Decimal

from app.database.connection import get_db_connection
from app.schemas.shop import DashboardStats, OrderSummary
from app.core.security import require_admin

api_router = APIRouter(prefix="/dashboard", tags=["shop-dashboard"])


@api_router.get("", response_model=DashboardStats)
async def get_dashboard(db=Depends(get_db_connection), _=Depends(require_admin)):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT COUNT(*) AS total FROM users")
        total_users = (await cur.fetchone())["total"]

        await cur.execute("SELECT COUNT(*) AS total FROM shop_orders")
        total_orders = (await cur.fetchone())["total"]

        await cur.execute(
            "SELECT COALESCE(SUM(total_amount), 0) AS revenue FROM shop_orders "
            "WHERE status IN ('paid', 'shipped', 'delivered')"
        )
        total_revenue = (await cur.fetchone())["revenue"]

        await cur.execute(
            "SELECT * FROM shop_orders ORDER BY created_at DESC LIMIT 10"
        )
        recent_rows = await cur.fetchall()

    return DashboardStats(
        total_users=total_users,
        total_orders=total_orders,
        total_revenue=Decimal(str(total_revenue)),
        recent_orders=[OrderSummary(**r) for r in recent_rows],
    )
