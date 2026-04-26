from fastapi import APIRouter, Depends, Query
from psycopg.rows import dict_row
from decimal import Decimal

from app.database.connection import get_db_connection
from app.schemas.shop import CouponUsageSummary, DashboardStats, LowStockVariant, OrderSummary, PendingOrderAlert, ShopAnalyticsOverview, TopProduct
from app.core.security import require_admin
from app.utils.responses import success

api_router = APIRouter(prefix="/dashboard", tags=["shop-dashboard"])


@api_router.get("")
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

        await cur.execute("SELECT * FROM shop_orders ORDER BY created_at DESC LIMIT 10")
        recent_rows = await cur.fetchall()

    data = DashboardStats(
        total_users=total_users,
        total_orders=total_orders,
        total_revenue=Decimal(str(total_revenue)),
        recent_orders=[OrderSummary(**r) for r in recent_rows],
    )
    return success(data)


@api_router.get("/analytics")
async def get_shop_analytics(
    low_stock_threshold: int = Query(default=5, ge=0),
    pending_days_threshold: int = Query(default=3, ge=1),
    top_n: int = Query(default=10, ge=1, le=50),
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT status, COUNT(*) AS cnt FROM shop_orders GROUP BY status")
        orders_by_status = {r["status"]: r["cnt"] for r in await cur.fetchall()}

        await cur.execute(
            "SELECT COALESCE(SUM(total_amount), 0) AS revenue FROM shop_orders "
            "WHERE status IN ('paid', 'shipped', 'delivered') "
            "AND DATE_TRUNC('month', created_at) = DATE_TRUNC('month', NOW())"
        )
        revenue_month = Decimal(str((await cur.fetchone())["revenue"]))

        await cur.execute(
            """
            SELECT p.id AS product_id, p.name AS product_name,
                   SUM(oi.quantity) AS total_sold,
                   SUM(oi.quantity * oi.unit_price) AS total_revenue
            FROM order_items oi
            JOIN product_variants pv ON pv.id = oi.product_variant_id
            JOIN products p ON p.id = pv.product_id
            JOIN shop_orders o ON o.id = oi.order_id
            WHERE o.status IN ('paid', 'shipped', 'delivered')
            GROUP BY p.id, p.name
            ORDER BY total_sold DESC
            LIMIT %s
            """,
            (top_n,),
        )
        top_products = [TopProduct(**r) for r in await cur.fetchall()]

        await cur.execute(
            """
            SELECT pv.id AS variant_id, pv.product_id, p.name AS product_name,
                   pv.name AS variant_name, pv.sku, pv.stock_quantity
            FROM product_variants pv
            JOIN products p ON p.id = pv.product_id
            WHERE pv.stock_quantity <= %s AND pv.is_active = true
            ORDER BY pv.stock_quantity ASC
            """,
            (low_stock_threshold,),
        )
        low_stock = [LowStockVariant(**r) for r in await cur.fetchall()]

        await cur.execute(
            "SELECT *, "
            "CASE WHEN max_uses > 0 THEN ROUND(uses_count::numeric / max_uses * 100, 1) "
            "     ELSE 0 END AS usage_rate "
            "FROM coupons WHERE is_active = true ORDER BY uses_count DESC"
        )
        coupons = [CouponUsageSummary(**r) for r in await cur.fetchall()]

        await cur.execute(
            """
            SELECT id AS order_id, user_id, total_amount, created_at,
                   EXTRACT(DAY FROM NOW() - created_at)::int AS pending_since_days
            FROM shop_orders
            WHERE status = 'pending'
              AND created_at <= NOW() - (%s || ' days')::interval
            ORDER BY created_at ASC
            """,
            (str(pending_days_threshold),),
        )
        pending_alerts = [PendingOrderAlert(**r) for r in await cur.fetchall()]

    data = ShopAnalyticsOverview(
        orders_by_status=orders_by_status,
        revenue_current_month=revenue_month,
        top_products=top_products,
        low_stock_variants=low_stock,
        coupons=coupons,
        pending_alerts=pending_alerts,
    )
    return success(data)
