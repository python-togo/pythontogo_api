from fastapi import APIRouter, BackgroundTasks, Depends, status, HTTPException

from app.utils.contact import (
    add_contact, get_contact_by_id, get_all_contacts, update_contact, delete_contact)

from app.schemas.models import (
    ContactMessageSummary,
    MessageResponse,
    ContactMessageUpdate,
    ContactBase,

)
from app.database.connection import get_db_connection
from app.core.settings import logger


api_router = APIRouter(prefix="/contacts", tags=["contacts"])


@api_router.get("/", response_model=list[ContactMessageSummary])
async def _get_all_contacts(db=Depends(get_db_connection)):
    try:
        contacts = await get_all_contacts(db)
        if not contacts:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No contacts found")
        return contacts
    except Exception as e:
        logger.error(f"Error retrieving contacts: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail="Error retrieving contacts")


@api_router.get("/{contact_id}", response_model=ContactMessageSummary)
async def _get_contact_by_id(contact_id: str, db=Depends(get_db_connection)):
    try:
        contact = await get_contact_by_id(db, contact_id)
        if not contact:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Contact with id {contact_id} not found")
        return contact
    except Exception as e:
        logger.error(
            f"Error retrieving contact with id {contact_id}: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail="Error retrieving contact")


@api_router.post("/send", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_contact_message(payload: ContactBase, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    """Add a new contact message."""
    try:
        result = await add_contact(db, payload.model_dump(), background_tasks)
        return result
    except Exception as e:
        logger.error(f"Error adding contact message: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail="Error adding contact message")


@api_router.put("/{contact_id}", response_model=MessageResponse)
async def _update_contact(contact_id: str, payload: ContactMessageUpdate, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:
        data_to_update = {k: v for k,
                          v in payload.model_dump().items() if v is not None}

        result = await update_contact(db, contact_id, data_to_update, background_tasks)
        return result
    except Exception as e:
        logger.error(f"Error updating contact: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail="Error updating contact")


@api_router.delete("/{contact_id}", response_model=MessageResponse)
async def _delete_contact(contact_id: str, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:
        result = await delete_contact(db, contact_id, background_tasks)
        return result
    except Exception as e:
        logger.error(f"Error deleting contact: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail="Error deleting contact")
