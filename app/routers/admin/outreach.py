from fastapi import APIRouter, Depends
from psycopg.rows import dict_row

from app.core.security import require_admin
from app.database.connection import get_db_connection
from app.schemas.models import (
    ContactMessageSummary,
    OutreachOverview,
    PartnerSponsorSummary,
)

api_router = APIRouter(prefix="/outreach", tags=["admin-outreach"])


@api_router.get("/overview", response_model=OutreachOverview)
async def get_outreach_overview(
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT COUNT(*) AS total FROM contact_messages")
        total_contacts = (await cur.fetchone())["total"]

        await cur.execute(
            "SELECT COUNT(*) AS total FROM contact_messages WHERE is_resolved = false"
        )
        unresolved = (await cur.fetchone())["total"]

        await cur.execute("SELECT COUNT(*) AS total FROM sponsors_partners")
        total_partners = (await cur.fetchone())["total"]

        await cur.execute(
            "SELECT COUNT(*) AS total FROM sponsors_partners WHERE is_confirmed = false"
        )
        unconfirmed = (await cur.fetchone())["total"]

        await cur.execute(
            "SELECT partner_type, COUNT(*) AS cnt FROM sponsors_partners GROUP BY partner_type"
        )
        by_type_rows = await cur.fetchall()

        await cur.execute(
            "SELECT package_tier, COUNT(*) AS cnt FROM sponsors_partners "
            "WHERE package_tier IS NOT NULL GROUP BY package_tier"
        )
        by_tier_rows = await cur.fetchall()

    return OutreachOverview(
        total_contacts=total_contacts,
        unresolved_contacts=unresolved,
        total_partners=total_partners,
        unconfirmed_partners=unconfirmed,
        partners_by_type={r["partner_type"]: r["cnt"] for r in by_type_rows},
        partners_by_tier={r["package_tier"]: r["cnt"] for r in by_tier_rows},
    )


@api_router.get("/contacts/unresolved", response_model=list[ContactMessageSummary])
async def list_unresolved_contacts(
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT * FROM contact_messages WHERE is_resolved = false "
            "ORDER BY created_at ASC"
        )
        rows = await cur.fetchall()
    return [ContactMessageSummary(**r) for r in rows]


@api_router.get("/partners/unconfirmed", response_model=list[PartnerSponsorSummary])
async def list_unconfirmed_partners(
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT * FROM sponsors_partners WHERE is_confirmed = false "
            "ORDER BY created_at ASC"
        )
        rows = await cur.fetchall()
    return [PartnerSponsorSummary(**r) for r in rows]
