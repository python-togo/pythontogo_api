from fastapi import APIRouter, BackgroundTasks, Depends, status, HTTPException
from app.utils.sessions import (add_session, get_sessions_by_event,
                                get_session_by_id, get_all_sessions, update_session, delete_session)
from app.schemas.models import (
    MessageResponse,
    SessionBase,
    SessionUpdate,
    SessionSummary,
    SessionCreate
)

router = APIRouter(prefix="/sessions", tags=["sessions"])
