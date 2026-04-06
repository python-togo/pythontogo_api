from fastapi import APIRouter, BackgroundTasks, Depends, status, HTTPException
from app.utils.event import (
    add_event, get_events, get_event_by_code, update_event, delete_event)
from app.schemas.models import (
    EventBase, EventSummary, EventUpdate, MessageResponse)
from app.core.settings import logger


from app.database.connection import get_db_connection

api_router = APIRouter(prefix="/events", tags=["events"])


@api_router.post("/create", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_event(event: EventBase, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:

        result = await add_event(db, event.model_dump(), background_tasks)
        return result
    except Exception as e:
        logger.error(f"Error adding event: {str(e)}")
        # TODO - logging the error can be done here
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error creating event")


@api_router.get("/list", response_model=list[EventSummary])
async def list_events(db=Depends(get_db_connection)):
    try:
        events = await get_events(db)
        if not events:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No events found")
        return events
    except Exception as e:
        logger.error(f"Error retrieving events: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error retrieving events")


@api_router.get("/get/{event_code}", response_model=EventSummary)
async def get_event(event_code: str, db=Depends(get_db_connection)):
    try:
        event_code = event_code.upper()
        event = await get_event_by_code(db, event_code)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Event with code {event_code} not found")
        return event
    except Exception as e:
        logger.error(f"Error retrieving event: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error retrieving event")


@api_router.put("/update/{event_code}", response_model=MessageResponse)
async def update_event_details(event_code: str, event_update: EventUpdate,  background_tasks: BackgroundTasks, db=Depends(get_db_connection),):
    try:
        event_code = event_code.upper()
        event_data_to_update = {
            k: v for k, v in event_update.model_dump().items() if v is not None}
        result = await update_event(db, event_code, event_data_to_update, background_tasks)
        return result
    except Exception as e:
        logger.error(f"Error updating event: {str(e)}")
        # TODO - logging the error can be done here
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error updating event")


@api_router.delete("/delete/{event_code}", response_model=MessageResponse)
async def delete_event_by_code(event_code: str, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:
        event_code = event_code.upper()
        result = await delete_event(db, event_code, background_tasks)
        return result
    except Exception as e:
        logger.error(f"Error deleting event: {str(e)}")

        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error deleting event")
