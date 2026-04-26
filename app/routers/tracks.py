from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from app.database.connection import get_db_connection
from app.utils.tracks import add_track, get_track_by_id, update_track, delete_track
from app.schemas.models import TrackCreate, TrackUpdate
from app.core.settings import logger
from app.utils.responses import success
from app.utils.pagination import paginate

api_router = APIRouter(prefix="/tracks", tags=["tracks"])


@api_router.post("/create/{event_code}", status_code=status.HTTP_201_CREATED)
async def create_track(track: TrackCreate, event_code: str, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:
        result = await add_track(db, track, event_code, background_tasks)
        return success(result, code=201)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.get("/list/{event_code}")
async def list_tracks(
    event_code: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
):
    try:
        rows, total = await paginate(
            db,
            """
            SELECT t.*
            FROM tracks t
            JOIN events e ON t.event_id = e.id
            WHERE e.code = %s
            ORDER BY t.created_at DESC
            """,
            (event_code.strip().upper(),),
            page, per_page,
        )
        if not rows and page == 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No tracks found for this event")
        return success(rows, total=total, page=page, per_page=per_page)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.get("/list")
async def list_all_tracks(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
):
    try:
        rows, total = await paginate(
            db,
            "SELECT * FROM tracks ORDER BY created_at DESC",
            (),
            page, per_page,
        )
        if not rows and page == 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No tracks found")
        return success(rows, total=total, page=page, per_page=per_page)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving tracks: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.get("/{track_id}")
async def get_track(track_id: str, db=Depends(get_db_connection)):
    try:
        track = await get_track_by_id(db, track_id)
        if not track:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Track with id {track_id} not found")
        return success(track)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.put("/update/{track_id}")
async def update_track_details(track_id: str, track_update: TrackUpdate, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:
        result = await update_track(db, track_id, track_update, background_tasks)
        return success(result)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.delete("/delete/{track_id}")
async def delete_track_by_id(track_id: str, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:
        result = await delete_track(db, track_id, background_tasks)
        return success(result)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")
