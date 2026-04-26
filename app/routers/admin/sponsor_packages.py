from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.security import require_admin
from app.database.connection import get_db_connection
from app.schemas.models import PartnerSponsorSummary, SponsorPackageCreate, SponsorPackageSummary, SponsorPackageUpdate
from app.utils.sponsor_packages import (
    assign_package_to_sponsor,
    create_package,
    delete_package,
    get_package_by_id,
    get_packages_by_event,
    update_package,
)
from app.utils.responses import success

api_router = APIRouter(prefix="/sponsor-packages", tags=["admin-sponsor-packages"])


@api_router.get("/event/{event_code}")
async def list_packages(event_code: str, db=Depends(get_db_connection), _=Depends(require_admin)):
    return success(await get_packages_by_event(db, event_code))


@api_router.post("/event/{event_code}", status_code=status.HTTP_201_CREATED)
async def create_sponsor_package(
    event_code: str,
    payload: SponsorPackageCreate,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    data = await create_package(db, event_code, payload.model_dump(mode="json"))
    return success(data, code=201)


@api_router.get("/{package_id}")
async def get_package(package_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    return success(await get_package_by_id(db, str(package_id)))


@api_router.put("/{package_id}")
async def update_sponsor_package(
    package_id: UUID,
    payload: SponsorPackageUpdate,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    data = await update_package(db, str(package_id), payload.model_dump(mode="json", exclude_none=True))
    return success(data)


@api_router.delete("/{package_id}")
async def delete_sponsor_package(package_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    await delete_package(db, str(package_id))
    return success({"message": "Package deleted"})


@api_router.patch("/sponsors/{sponsor_id}/assign")
async def assign_package(
    sponsor_id: UUID,
    package_id: UUID | None = None,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    data = await assign_package_to_sponsor(db, str(sponsor_id), str(package_id) if package_id else None)
    return success(data)
