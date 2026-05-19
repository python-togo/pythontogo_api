from app.database.orm import select, insert, update, delete, select_with_join
from app.schemas.models import ProposalFormatCreate, ProposalFormatUpdate
from fastapi import BackgroundTasks, HTTPException
from uuid import uuid4
from app.utils.helpers import remove_null_values
from app.core.settings import logger


async def get_all_formats(db):
    """
    Retrieve all formats from the database.
    """
    try:
        formats = await select(db, "proposal_formats")
        if not formats:
            raise HTTPException(status_code=404, detail="No formats found")
        return formats
    except Exception as e:
        logger.error(f"Error retrieving formats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error: ")


async def get_formats_by_event(db, event_code):
    """
    Retrieve all formats for a specific event.
    """
    try:
        event_code = event_code.strip().upper()

        formats = await select_with_join(db, table="proposal_formats", join_table="events",
                                         join_condition="proposal_formats.event_id = events.id",
                                         columns=["proposal_formats.id", "proposal_formats.name_fr", "proposal_formats.name_en",
                                                  "proposal_formats.description_fr", "proposal_formats.description_en",
                                                  "proposal_formats.event_id", "proposal_formats.created_at", "proposal_formats.updated_at"],
                                         filter={"events.code": event_code})

        if not formats:
            raise HTTPException(
                status_code=404, detail="No formats found for the specified event or event does not exist")
        return formats
    except Exception as e:
        logger.error(f"Error retrieving formats: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error: ")


async def get_format_by_id(db, format_id):
    """
    Retrieve a format by its ID.
    """
    try:
        format = await select(db, "proposal_formats", filter={"id": format_id})
        if not format:
            raise HTTPException(status_code=404, detail="Format not found")
        return format[0]
    except Exception as e:
        logger.error(f"Error retrieving format: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


async def add_format(db, format: ProposalFormatCreate, event_code: str, background_tasks: BackgroundTasks):
    """
    Add a new format to the database.
    """
    try:
        event_code = event_code.strip().upper()
        format_data = format.model_dump(mode="json")
        event_data = await select(db, "events", filter={"code": event_code})
        if not event_data:
            raise HTTPException(status_code=404, detail="Event not found")
        event_id = event_data[0]["id"]
        existing_formats = await select(db, "proposal_formats", filter={
            "name_fr": format_data["name_fr"], "event_id": event_id, "name_en": format_data["name_en"]})
        if existing_formats:
            raise HTTPException(
                status_code=400, detail="Formats already exists for this event")

        format_data.update({
            "id": str(uuid4()),
            "event_id": event_id,
        })
        background_tasks.add_task(insert, db, "proposal_formats", format_data)

        return {"message": "formats created successfully"}
    except Exception as e:
        logger.error(f"Error adding formats: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


async def update_format(db, format_id, format: ProposalFormatUpdate, background_tasks: BackgroundTasks):
    """
    Update an existing format in the database.
    """
    try:
        format_data = remove_null_values(format.model_dump(mode="json"))
        existing_formats = await select(db, "proposal_formats", filter={"id": format_id})
        if not existing_formats:
            raise HTTPException(status_code=404, detail="Format not found")

        background_tasks.add_task(update, db, "proposal_formats", format_data,
                                  filter={"id": format_id})
        return {"message": "formats updated successfully"}
    except Exception as e:
        logger.error(f"Error updating formats: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


async def delete_format(db, format_id, background_tasks: BackgroundTasks):
    """
    Delete a formats from the database.
    """
    try:
        existing_formats = await select(db, "proposal_formats", filter={"id": format_id})
        if not existing_formats:
            raise HTTPException(status_code=404, detail="formats not found")

        background_tasks.add_task(
            delete, db, "proposal_formats", filter={"id": format_id})
        return {"message": "formats deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting formats: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")
