from uuid import uuid4

from app.database.orm import select, insert, update, delete
from fastapi import BackgroundTasks, HTTPException, status
from app.core.settings import logger
from app.utils.helpers import remove_null_values


async def add_event(db, new_event: dict, background_tasks: BackgroundTasks):
    try:
        existing = await select(db, "events", filter={"code": new_event["code"].strip().upper()})

        if existing:
            logger.warning(
                f"Attempt to add duplicate event with code {new_event['code']}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Event with code {new_event['code']} already exists")
        new_event.update({
            "id": str(uuid4()),
            "code": new_event["code"].strip().upper()
        })

        background_tasks.add_task(insert, db, "events", new_event)
        return {"message": "Event created successfully"}
    except Exception as e:
        logger.error(f"Error adding event: {str(e)}")
        # TODO - Send email to admin about error during processing the request
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error adding event")


async def delete_event(db, event_id: str, background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(
            delete, db, "events", filter={"id": event_id})
        return {"message": "Event deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting event: {str(e)}")
        # TODO - Send email to admin about error during processing the request
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error deleting event")


async def get_event_by_code(db, event_code: str):
    try:
        event_code = event_code.strip().upper()
        event = await select(db, "events", filter={"code": event_code})
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Event with code {event_code} not found")
        return event[0]
    except Exception as e:
        # TODO sending email to admin about error during processing the request can be done here
        logger.error(f"Error retrieving event: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error retrieving event")


async def get_events(db):
    try:
        events = await select(db, "events")
        if not events:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No events found")
        return events
    except Exception as e:
        # logging the error can be done here
        # TODO: Send email to admin about error during processing the request
        logger.error(f"Error retrieving events: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error retrieving events")


async def update_event(db, event_code: str, payload: dict, background_tasks: BackgroundTasks):
    try:
        event_code = event_code.strip().upper()
        existing = await select(db, "events", filter={"code": event_code})
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Event with code {event_code} not found")
        payload = remove_null_values(payload)
        background_tasks.add_task(
            update, db, "events", payload, filter={"code": event_code})
        return {"message": "Event updated successfully"}
    except Exception as e:
        logger.error(f"Error updating event: {str(e)}")
        # TODO - Send email to admin about error during processing the request
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error updating event")
