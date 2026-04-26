from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from app.core.cloudinary import upload_image
from app.core.security import require_admin
from app.database.connection import get_db_connection
from app.schemas.models import SpeakerCreate, SpeakerSummary, SpeakerUpdate
from app.utils.speaker import (
    add_speaker,
    delete_speaker,
    get_speaker_by_id,
    update_speaker,
    update_speaker_photo,
)
from app.utils.responses import success
from app.utils.pagination import paginate

api_router = APIRouter(prefix="/speakers", tags=["admin-speakers"])


@api_router.get("")
async def list_all_speakers(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    rows, total = await paginate(
        db,
        "SELECT * FROM speakers ORDER BY created_at DESC",
        (),
        page, per_page,
    )
    return success(rows, total=total, page=page, per_page=per_page)


@api_router.get("/event/{event_code}")
async def list_speakers_by_event(
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
        FROM speakers s
        JOIN events e ON s.event_id = e.id
        WHERE e.code = %s
        ORDER BY s.created_at DESC
        """,
        (event_code.strip().upper(),),
        page, per_page,
    )
    return success(rows, total=total, page=page, per_page=per_page)


@api_router.post("/event/{event_code}", status_code=status.HTTP_201_CREATED)
async def create_speaker(
    event_code: str,
    payload: SpeakerCreate,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    data = payload.model_dump(mode="json", exclude_none=True)
    return success(await add_speaker(db, event_code, data), code=201)


@api_router.get("/{speaker_id}")
async def get_speaker(speaker_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    return success(await get_speaker_by_id(db, str(speaker_id)))


@api_router.put("/{speaker_id}")
async def update_speaker_details(
    speaker_id: UUID,
    payload: SpeakerUpdate,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    data = payload.model_dump(mode="json", exclude_none=True)
    return success(await update_speaker(db, str(speaker_id), data))


@api_router.post("/{speaker_id}/photo")
async def upload_speaker_photo(
    speaker_id: UUID,
    file: UploadFile = File(...),
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    photo_url = await upload_image(file, subfolder="speakers", public_id=str(speaker_id))
    return success(await update_speaker_photo(db, str(speaker_id), photo_url))


@api_router.delete("/{speaker_id}")
async def delete_speaker_by_id(speaker_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    await delete_speaker(db, str(speaker_id))
    return success({"message": "Speaker deleted"})
