from fastapi import HTTPException, BackgroundTasks
from app.core.settings import logger

from app.database.orm import select, insert, update, delete


async def add_contact(db, payload: dict, background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(insert, db, "contact_messages", payload)
        return {"message": "Contact message received successfully"}
    except Exception as e:
        logger.error(f"Error adding contact message: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail="Error adding contact message")


async def delete_contact(db, contact_id: str, background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(
            delete, db, "contact_messages", filter={"id": contact_id})
        return {"message": "Contact deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting contact: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Error deleting contact")


async def get_contact_by_id(db, contact_id: str):
    try:
        contact = await select(db, "contact_messages", filter={"id": contact_id})
        if not contact:
            logger.error(f"Contact with id {contact_id} not found")
        return contact[0]
    except Exception as e:
        logger.error(f"Error retrieving contact: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Error retrieving contact")


async def get_all_contacts(db):
    try:
        contacts = await select(db, "contact_messages")
        return contacts
    except Exception as e:
        logger.error(f"Error retrieving all contacts: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail="Error retrieving all contacts")


async def update_contact(db, contact_id: str, payload: dict, background_tasks: BackgroundTasks):
    try:
        existing = await select(db, "contact_messages", filter={"id": contact_id})
        if not existing:
            logger.error(f"Contact with id {contact_id} not found")
            raise HTTPException(
                status_code=404, detail=f"Contact with id {contact_id} not found")
        background_tasks.add_task(
            update, db, "contact_messages", payload, filter={"id": contact_id})
        return {"message": "Contact updated successfully"}
    except Exception as e:
        logger.error(f"Error updating contact: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Error updating contact")
