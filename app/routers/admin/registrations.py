from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.security import require_admin
from app.database.connection import get_db_connection
from app.schemas.models import (
    RegistrationCreate,
    RegistrationsDashboard,
    RegistrationStatusUpdate,
    RegistrationSummary,
    RegistrationUpdate,
)
from app.utils.registrations import (
    delete_registration,
    get_registration_by_id,
    get_registrations_by_event,
    get_registrations_dashboard,
    register_participant,
    update_registration,
    update_registration_status,
)

api_router = APIRouter(prefix="/registrations", tags=["admin-registrations"])


@api_router.get("/{event_code}/dashboard", response_model=RegistrationsDashboard)
async def registrations_dashboard(
    event_code: str,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    return await get_registrations_dashboard(db, event_code)


@api_router.get("/{event_code}", response_model=list[RegistrationSummary])
async def list_registrations(
    event_code: str,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    return await get_registrations_by_event(db, event_code)


@api_router.post("/{event_code}", response_model=RegistrationSummary, status_code=status.HTTP_201_CREATED)
async def create_registration(
    event_code: str,
    payload: RegistrationCreate,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    return await register_participant(db, event_code, payload.model_dump())


@api_router.get("/detail/{registration_id}", response_model=RegistrationSummary)
async def get_registration(
    registration_id: UUID,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    return await get_registration_by_id(db, str(registration_id))


@api_router.put("/{registration_id}", response_model=RegistrationSummary)
async def update_registration_details(
    registration_id: UUID,
    payload: RegistrationUpdate,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    data = payload.model_dump(exclude_none=True)
    return await update_registration(db, str(registration_id), data)


@api_router.patch("/{registration_id}/status", response_model=RegistrationSummary)
async def change_registration_status(
    registration_id: UUID,
    payload: RegistrationStatusUpdate,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    return await update_registration_status(db, str(registration_id), payload.status.value)


@api_router.delete("/{registration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_registration(
    registration_id: UUID,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    await delete_registration(db, str(registration_id))
