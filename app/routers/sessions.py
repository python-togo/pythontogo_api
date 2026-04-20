from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.security import require_admin
from app.database.connection import get_db_connection
from app.schemas.models import (
    MessageResponse,
    SessionCreate,
    SessionSummary,
    SessionUpdate,
)
from app.utils.sessions import (
    add_session,
    delete_session,
    get_all_sessions,
    get_session_by_id,
    get_sessions_by_event,
    get_sessions_schedule,
    update_session,
)

router = APIRouter(prefix="/sessions", tags=["admin-sessions"])


@router.get("", response_model=list[SessionSummary])
async def list_all_sessions(
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    return await get_all_sessions(db)


@router.get("/event/{event_code}", response_model=list[SessionSummary])
async def list_sessions_by_event(
    event_code: str,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    return await get_sessions_by_event(db, event_code)


@router.get("/event/{event_code}/schedule")
async def get_event_schedule(
    event_code: str,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    """Programme complet : sessions triées par horaire avec speaker et track."""
    return await get_sessions_schedule(db, event_code)


@router.post("/event/{event_code}", response_model=SessionSummary, status_code=status.HTTP_201_CREATED)
async def create_session(
    event_code: str,
    payload: SessionCreate,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    data = payload.model_dump(mode="json", exclude_none=True)
    return await add_session(db, event_code, data)


@router.get("/{session_id}", response_model=SessionSummary)
async def get_session(
    session_id: UUID,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    return await get_session_by_id(db, str(session_id))


@router.put("/{session_id}", response_model=SessionSummary)
async def update_session_details(
    session_id: UUID,
    payload: SessionUpdate,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    data = payload.model_dump(mode="json", exclude_none=True)
    return await update_session(db, str(session_id), data)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session_by_id(
    session_id: UUID,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    await delete_session(db, str(session_id))
