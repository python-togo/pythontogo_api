from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.security import require_admin
from app.database.connection import get_db_connection
from app.schemas.models import SessionCreate, SessionSummary, SessionUpdate
from app.utils.sessions import (
    add_session,
    delete_session,
    get_session_by_id,
    get_sessions_schedule,
    update_session,
)
from app.utils.responses import success
from app.utils.pagination import paginate

router = APIRouter(prefix="/sessions", tags=["admin-sessions"])


@router.get("")
async def list_all_sessions(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    rows, total = await paginate(
        db,
        "SELECT * FROM sessions ORDER BY created_at DESC",
        (),
        page, per_page,
    )
    return success(rows, total=total, page=page, per_page=per_page)


@router.get("/event/{event_code}")
async def list_sessions_by_event(
    event_code: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    rows, total = await paginate(
        db,
        """
        SELECT s.*
        FROM sessions s
        JOIN events e ON s.event_id = e.id
        WHERE e.code = %s
        ORDER BY s.start_time ASC
        """,
        (event_code.strip().upper(),),
        page, per_page,
    )
    return success(rows, total=total, page=page, per_page=per_page)


@router.get("/event/{event_code}/schedule")
async def get_event_schedule(event_code: str, db=Depends(get_db_connection), _=Depends(require_admin)):
    return success(await get_sessions_schedule(db, event_code))


@router.post("/event/{event_code}", status_code=status.HTTP_201_CREATED)
async def create_session(
    event_code: str,
    payload: SessionCreate,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    data = payload.model_dump(mode="json", exclude_none=True)
    return success(await add_session(db, event_code, data), code=201)


@router.get("/{session_id}")
async def get_session(session_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    return success(await get_session_by_id(db, str(session_id)))


@router.put("/{session_id}")
async def update_session_details(
    session_id: UUID,
    payload: SessionUpdate,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    data = payload.model_dump(mode="json", exclude_none=True)
    return success(await update_session(db, str(session_id), data))


@router.delete("/{session_id}")
async def delete_session_by_id(session_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    await delete_session(db, str(session_id))
    return success({"message": "Session deleted"})
