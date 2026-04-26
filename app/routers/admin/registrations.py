from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.security import require_admin
from app.database.connection import get_db_connection
from app.schemas.models import RegistrationCreate, RegistrationsDashboard, RegistrationStatusUpdate, RegistrationSummary, RegistrationUpdate
from app.utils.registrations import (
    delete_registration,
    get_registration_by_id,
    get_registrations_dashboard,
    register_participant,
    update_registration,
    update_registration_status,
)
from app.utils.responses import success
from app.utils.pagination import paginate

api_router = APIRouter(prefix="/registrations", tags=["admin-registrations"])


@api_router.get("/{event_code}/dashboard")
async def registrations_dashboard(
    event_code: str,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    data = await get_registrations_dashboard(db, event_code)
    return success(data)


@api_router.get("/{event_code}")
async def list_registrations(
    event_code: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    rows, total = await paginate(
        db,
        """
        SELECT r.*
        FROM registrations r
        JOIN events e ON r.event_id = e.id
        WHERE e.code = %s
        ORDER BY r.created_at DESC
        """,
        (event_code.strip().upper(),),
        page, per_page,
    )
    return success(rows, total=total, page=page, per_page=per_page)


@api_router.post("/{event_code}", status_code=status.HTTP_201_CREATED)
async def create_registration(
    event_code: str,
    payload: RegistrationCreate,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    data = await register_participant(db, event_code, payload.model_dump())
    return success(data, code=201)


@api_router.get("/detail/{registration_id}")
async def get_registration(
    registration_id: UUID,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    data = await get_registration_by_id(db, str(registration_id))
    return success(data)


@api_router.put("/{registration_id}")
async def update_registration_details(
    registration_id: UUID,
    payload: RegistrationUpdate,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    data = await update_registration(db, str(registration_id), payload.model_dump(exclude_none=True))
    return success(data)


@api_router.patch("/{registration_id}/status")
async def change_registration_status(
    registration_id: UUID,
    payload: RegistrationStatusUpdate,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    data = await update_registration_status(db, str(registration_id), payload.status.value)
    return success(data)


@api_router.delete("/{registration_id}")
async def remove_registration(
    registration_id: UUID,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    await delete_registration(db, str(registration_id))
    return success({"message": "Registration deleted"})
