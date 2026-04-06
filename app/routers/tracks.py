from fastapi import APIRouter, BackgroundTasks, Depends, status, HTTPException
from app.database.connection import get_db_connection
from app.utils.tracks import (add_track, get_tracks_by_event,
                              get_track_by_id, get_all_tracks, update_track, delete_track)
from app.schemas.models import (
    MessageResponse,
    TrackCreate,
    TrackSummary,
    TrackUpdate,
)
from app.core.settings import logger

api_router = APIRouter(prefix="/tracks", tags=["tracks"])


@api_router.post("/create/{event_code}", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_track(track: TrackCreate, event_code: str, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    """
    Create a new track for an event.
    """
    try:
        result = await add_track(db, track, event_code, background_tasks)
        return result
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.get("/list/{event_code}", response_model=list[TrackSummary])
async def list_tracks(event_code: str, db=Depends(get_db_connection)):
    """
    List all tracks for a specific event.
    """
    try:
        tracks = await get_tracks_by_event(db, event_code)
        if not tracks:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No tracks found for this event")
        return tracks
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.get("/list", response_model=list[TrackSummary])
async def list_all_tracks(db=Depends(get_db_connection)):
    """
    List all tracks across all events.
    """
    try:
        tracks = await get_all_tracks(db)
        if not tracks:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No tracks found")
        return tracks
    except Exception as e:
        logger.error(f"Error retrieving tracks: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.get("/{track_id}", response_model=TrackSummary)
async def get_track(track_id: str, db=Depends(get_db_connection)):
    """
    Get a track by its ID.
    """
    try:
        track = await get_track_by_id(db, track_id)
        if not track:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Track with id {track_id} not found")
        return track
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.put("/update/{track_id}", response_model=MessageResponse)
async def update_track_details(track_id: str, track_update: TrackUpdate, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    """
    Update details of an existing track.
    """
    try:
        result = await update_track(db, track_id, track_update, background_tasks)
        return result
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.delete("/delete/{track_id}", response_model=MessageResponse)
async def delete_track_by_id(track_id: str, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    """
    Delete a track by its ID.
    """
    try:
        result = await delete_track(db, track_id, background_tasks)
        return result
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")
