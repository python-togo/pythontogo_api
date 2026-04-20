from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.core.cloudinary import upload_image
from app.core.security import require_admin
from app.database.connection import get_db_connection
from app.schemas.models import SpeakerCreate, SpeakerSummary, SpeakerUpdate
from app.utils.speaker import (
    add_speaker,
    delete_speaker,
    get_all_speakers,
    get_speaker_by_id,
    get_speakers_by_event,
    update_speaker,
    update_speaker_photo,
)

api_router = APIRouter(prefix="/speakers", tags=["admin-speakers"])


@api_router.get("", response_model=list[SpeakerSummary])
async def list_all_speakers(
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    return await get_all_speakers(db)


@api_router.get("/event/{event_code}", response_model=list[SpeakerSummary])
async def list_speakers_by_event(
    event_code: str,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    return await get_speakers_by_event(db, event_code)


@api_router.post("/event/{event_code}", response_model=SpeakerSummary, status_code=status.HTTP_201_CREATED)
async def create_speaker(
    event_code: str,
    payload: SpeakerCreate,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    data = payload.model_dump(mode="json", exclude_none=True)
    return await add_speaker(db, event_code, data)


@api_router.get("/{speaker_id}", response_model=SpeakerSummary)
async def get_speaker(
    speaker_id: UUID,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    return await get_speaker_by_id(db, str(speaker_id))


@api_router.put("/{speaker_id}", response_model=SpeakerSummary)
async def update_speaker_details(
    speaker_id: UUID,
    payload: SpeakerUpdate,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    data = payload.model_dump(mode="json", exclude_none=True)
    return await update_speaker(db, str(speaker_id), data)


@api_router.post("/{speaker_id}/photo", response_model=SpeakerSummary)
async def upload_speaker_photo(
    speaker_id: UUID,
    file: UploadFile = File(...),
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    photo_url = await upload_image(file, subfolder="speakers", public_id=str(speaker_id))
    return await update_speaker_photo(db, str(speaker_id), photo_url)


@api_router.delete("/{speaker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_speaker_by_id(
    speaker_id: UUID,
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    await delete_speaker(db, str(speaker_id))
