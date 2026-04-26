from fastapi import APIRouter, Depends, status
from typing import Annotated

from app.core.security import get_current_user
from app.database.connection import get_db_connection
from app.schemas.models import AuthenticatedUser, RegistrationCreate
from app.utils.registrations import register_participant
from app.utils.responses import success

api_router = APIRouter(prefix="/registrations", tags=["registrations"])


@api_router.post("/{event_code}", status_code=status.HTTP_201_CREATED)
async def register_for_event(
    event_code: str,
    payload: RegistrationCreate,
    db=Depends(get_db_connection),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    data = await register_participant(db, event_code, payload.model_dump(), user_id=str(current_user.id))
    return success(data, code=201)
