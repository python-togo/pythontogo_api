from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from datetime import datetime, timezone

from psycopg.rows import dict_row

from app.utils.event import add_event, get_event_by_id, update_event, delete_event
from app.schemas.models import EventBase, EventUpdate
from app.core.settings import logger
from app.core.security import require_admin
from app.database.connection import get_db_connection
from app.schemas.models import EventDashboardItem, EventsDashboardOverview
from app.utils.responses import success
from app.utils.pagination import paginate

api_router = APIRouter(prefix="/events", tags=["admin-events"])


@api_router.get("/overview")
async def get_events_overview(
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    now = datetime.now(timezone.utc)

    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT
                e.id, e.code, e.title, e.start_date, e.end_date, e.is_active,
                e.cfp_open_at, e.cfp_close_at,
                COUNT(DISTINCT p.id)                                        AS total_proposals,
                COUNT(DISTINCT p.id) FILTER (WHERE p.status = 'accepted')   AS accepted_proposals,
                COUNT(DISTINCT sp.id) FILTER (WHERE sp.is_confirmed = true)  AS confirmed_sponsors,
                COUNT(DISTINCT spk.id)                                       AS total_speakers,
                COUNT(DISTINCT s.id)                                         AS total_sessions
            FROM events e
            LEFT JOIN proposals p   ON p.event_id = e.id
            LEFT JOIN sponsors_partners sp ON sp.event_id = e.id
            LEFT JOIN speakers spk  ON spk.event_id = e.id
            LEFT JOIN sessions s    ON s.event_id = e.id
            GROUP BY e.id
            ORDER BY e.start_date DESC
            """
        )
        rows = await cur.fetchall()

        await cur.execute("SELECT COUNT(*) AS total FROM events")
        total_events = (await cur.fetchone())["total"]

        await cur.execute("SELECT COUNT(*) AS total FROM events WHERE is_active = true")
        active_events = (await cur.fetchone())["total"]

    items = []
    for r in rows:
        total_p = r["total_proposals"] or 0
        accepted_p = r["accepted_proposals"] or 0
        cfp_open_at = r["cfp_open_at"]
        cfp_close_at = r["cfp_close_at"]

        if cfp_open_at and cfp_open_at.tzinfo is None:
            cfp_open_at = cfp_open_at.replace(tzinfo=timezone.utc)
        if cfp_close_at and cfp_close_at.tzinfo is None:
            cfp_close_at = cfp_close_at.replace(tzinfo=timezone.utc)

        cfp_is_open = bool(cfp_open_at and cfp_close_at and cfp_open_at <= now <= cfp_close_at)
        acceptance_rate = round(accepted_p / total_p * 100, 1) if total_p else 0.0

        items.append(EventDashboardItem(
            id=r["id"],
            code=r["code"],
            title=r["title"],
            start_date=r["start_date"],
            end_date=r["end_date"],
            is_active=r["is_active"],
            cfp_is_open=cfp_is_open,
            total_proposals=total_p,
            accepted_proposals=accepted_p,
            acceptance_rate=acceptance_rate,
            confirmed_sponsors=r["confirmed_sponsors"] or 0,
            total_speakers=r["total_speakers"] or 0,
            total_sessions=r["total_sessions"] or 0,
        ))

    data = EventsDashboardOverview(
        total_events=total_events,
        active_events=active_events,
        events=items,
    )
    return success(data)

@api_router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_event(event: EventBase, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:
        result = await add_event(db, event.model_dump(mode="json"), background_tasks)
        return success(result, code=201)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding event: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating event")
    

@api_router.get("/list")
async def list_events(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
):
    try:
        rows, total = await paginate(
            db,
            "SELECT * FROM events ORDER BY created_at DESC",
            (),
            page, per_page,
        )
        if not rows and page == 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No events found")
        return success(rows, total=total, page=page, per_page=per_page)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving events: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving events")


@api_router.get("/get/{event_id}")
async def get_event(event_id: str, db=Depends(get_db_connection)):
    try:
        event = await get_event_by_id(db, event_id)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event with id {event_id} not found")
        return success(event)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving event: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving event")


@api_router.put("/update/{event_id}")
async def update_event_details(event_id: str, event_update: EventUpdate, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:
        data = {k: v for k, v in event_update.model_dump(mode="json").items() if v is not None}
        result = await update_event(db, event_id, data, background_tasks)
        return success(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating event: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating event")


@api_router.delete("/delete/{event_id}")
async def delete_event_by_id(event_id: str, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:
        result = await delete_event(db, event_id, background_tasks)
        return success(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting event: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting event")