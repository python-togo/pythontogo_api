from fastapi import APIRouter, Depends, Query
from psycopg.rows import dict_row

from app.core.security import require_admin
from app.database.connection import get_db_connection
from app.schemas.models import ProposalsDashboardOverview, ProposalSummary
from app.utils.responses import success
from app.utils.pagination import paginate

api_router = APIRouter(prefix="/proposals", tags=["admin-proposals"])


@api_router.get("/overview")
async def get_proposals_overview(
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT COUNT(*) AS total FROM proposals")
        total = (await cur.fetchone())["total"]

        await cur.execute("SELECT status, COUNT(*) AS cnt FROM proposals GROUP BY status")
        by_status = {r["status"]: r["cnt"] for r in await cur.fetchall()}

        await cur.execute("SELECT session_type, COUNT(*) AS cnt FROM proposals GROUP BY session_type")
        by_session_type = {r["session_type"]: r["cnt"] for r in await cur.fetchall()}

        await cur.execute("SELECT COUNT(*) AS total FROM proposals WHERE track_id IS NULL")
        without_track = (await cur.fetchone())["total"]

    data = ProposalsDashboardOverview(
        total_proposals=total,
        by_status=by_status,
        by_session_type=by_session_type,
        without_track=without_track,
    )
    return success(data)


@api_router.get("/by-status/{status}")
async def list_proposals_by_status(
    status: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    rows, total = await paginate(
        db,
        "SELECT * FROM proposals WHERE status = %s ORDER BY created_at DESC",
        (status,),
        page, per_page,
    )
    return success([ProposalSummary(**r) for r in rows], total=total, page=page, per_page=per_page)


@api_router.get("/without-track")
async def list_proposals_without_track(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    rows, total = await paginate(
        db,
        "SELECT * FROM proposals WHERE track_id IS NULL ORDER BY created_at ASC",
        (),
        page, per_page,
    )
    return success([ProposalSummary(**r) for r in rows], total=total, page=page, per_page=per_page)
