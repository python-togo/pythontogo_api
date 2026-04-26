from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends
from psycopg.rows import dict_row

from app.core.security import require_admin
from app.database.connection import get_db_connection, get_redis_client
from app.schemas.models import GlobalOverview
from app.utils.responses import success

api_router = APIRouter(prefix="/overview", tags=["admin-overview"])


@api_router.get("")
async def get_global_overview(
    db=Depends(get_db_connection),
    redis=Depends(get_redis_client),
    _=Depends(require_admin),
):
    today = date.today()

    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT COUNT(*) AS total, "
            "COUNT(*) FILTER (WHERE is_active = true) AS active "
            "FROM users"
        )
        u = await cur.fetchone()
        total_users, active_users = u["total"], u["active"]

        await cur.execute(
            "SELECT COUNT(*) AS total FROM users "
            "WHERE created_at >= NOW() - INTERVAL '7 days'"
        )
        new_users = (await cur.fetchone())["total"]

        await cur.execute("SELECT role, COUNT(*) AS cnt FROM users GROUP BY role")
        users_by_role = {r["role"]: r["cnt"] for r in await cur.fetchall()}

        await cur.execute(
            "SELECT COUNT(*) AS total, "
            "COUNT(*) FILTER (WHERE is_active = true)   AS active, "
            "COUNT(*) FILTER (WHERE end_date < %s)      AS past "
            "FROM events",
            (today,),
        )
        ev = await cur.fetchone()
        total_events, active_events, past_events = ev["total"], ev["active"], ev["past"]

        await cur.execute(
            "SELECT COUNT(*) AS total, "
            "COUNT(*) FILTER (WHERE status IN ('draft', 'submitted')) AS pending "
            "FROM proposals"
        )
        pr = await cur.fetchone()
        total_proposals, pending_proposals = pr["total"], pr["pending"]

        await cur.execute(
            "SELECT COUNT(*) AS total, "
            "COUNT(*) FILTER (WHERE status = 'confirmed') AS confirmed "
            "FROM registrations"
        )
        reg = await cur.fetchone()
        total_registrations, confirmed_registrations = reg["total"], reg["confirmed"]

        await cur.execute(
            "SELECT COUNT(*) FILTER (WHERE is_resolved = false)  AS unresolved_contacts, "
            "       (SELECT COUNT(*) FROM sponsors_partners WHERE is_confirmed = false) AS unconfirmed_partners "
            "FROM contact_messages"
        )
        out = await cur.fetchone()
        unresolved_contacts = out["unresolved_contacts"]
        unconfirmed_partners = out["unconfirmed_partners"]

        await cur.execute("SELECT status, COUNT(*) AS cnt FROM shop_orders GROUP BY status")
        orders_by_status = {r["status"]: r["cnt"] for r in await cur.fetchall()}
        total_orders = sum(orders_by_status.values())

        await cur.execute(
            "SELECT COALESCE(SUM(total_amount), 0) AS revenue FROM shop_orders "
            "WHERE status IN ('paid', 'shipped', 'delivered')"
        )
        total_revenue = Decimal(str((await cur.fetchone())["revenue"]))

        await cur.execute(
            "SELECT COALESCE(SUM(total_amount), 0) AS revenue FROM shop_orders "
            "WHERE status IN ('paid', 'shipped', 'delivered') "
            "AND DATE_TRUNC('month', created_at) = DATE_TRUNC('month', NOW())"
        )
        revenue_month = Decimal(str((await cur.fetchone())["revenue"]))

    active_sessions = len(await redis.keys("PYTOGO_REFRESH:*"))

    data = GlobalOverview(
        total_users=total_users,
        active_users=active_users,
        new_users_last_7_days=new_users,
        users_by_role=users_by_role,
        total_events=total_events,
        active_events=active_events,
        past_events=past_events,
        total_proposals=total_proposals,
        pending_proposals=pending_proposals,
        total_registrations=total_registrations,
        confirmed_registrations=confirmed_registrations,
        unresolved_contacts=unresolved_contacts,
        unconfirmed_partners=unconfirmed_partners,
        total_orders=total_orders,
        orders_by_status=orders_by_status,
        total_revenue=total_revenue,
        revenue_current_month=revenue_month,
        active_sessions=active_sessions,
    )
    return success(data)
