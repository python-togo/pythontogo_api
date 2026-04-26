from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from app.utils.event import add_event, get_event_by_code, update_event, delete_event
from app.schemas.models import EventBase, EventUpdate
from app.core.settings import logger
from app.database.connection import get_db_connection
from app.utils.responses import success
from app.utils.pagination import paginate

api_router = APIRouter(prefix="/events", tags=["events"])


@api_router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_event(event: EventBase, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:
        result = await add_event(db, event.model_dump(mode="json"), background_tasks)
        return success(result, code=201)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding event: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating event")


@api_router.get("/list")
async def list_events(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
):
    try:
        rows, total = await paginate(
            db,
            "SELECT * FROM events ORDER BY created_at DESC",
            (),
            page, per_page,
        )
        if not rows and page == 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No events found")
        return success(rows, total=total, page=page, per_page=per_page)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving events: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving events")


@api_router.get("/get/{event_code}")
async def get_event(event_code: str, db=Depends(get_db_connection)):
    try:
        event_code = event_code.strip().upper()
        event = await get_event_by_code(db, event_code)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event with code {event_code} not found")
        return success(event)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving event: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving event")


@api_router.put("/update/{event_code}")
async def update_event_details(event_code: str, event_update: EventUpdate, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:
        event_code = event_code.strip().upper()
        data = {k: v for k, v in event_update.model_dump(mode="json").items() if v is not None}
        result = await update_event(db, event_code, data, background_tasks)
        return success(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating event: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating event")


@api_router.delete("/delete/{event_code}")
async def delete_event_by_code(event_code: str, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:
        event_code = event_code.strip().upper()
        result = await delete_event(db, event_code, background_tasks)
        return success(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting event: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting event")
