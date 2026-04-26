from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from app.utils.contact import add_contact, get_contact_by_id, update_contact, delete_contact
from app.schemas.models import ContactBase, ContactMessageUpdate
from app.database.connection import get_db_connection
from app.core.settings import logger
from app.utils.responses import success
from app.utils.pagination import paginate

api_router = APIRouter(prefix="/contacts", tags=["contacts"])


@api_router.get("/")
async def _get_all_contacts(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
):
    try:
        rows, total = await paginate(
            db,
            "SELECT * FROM contact_messages ORDER BY created_at DESC",
            (),
            page, per_page,
        )
        if not rows and page == 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No contacts found")
        return success(rows, total=total, page=page, per_page=per_page)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving contacts: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving contacts")


@api_router.get("/{contact_id}")
async def _get_contact_by_id(contact_id: str, db=Depends(get_db_connection)):
    try:
        contact = await get_contact_by_id(db, contact_id)
        if not contact:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contact with id {contact_id} not found")
        return success(contact)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving contact with id {contact_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving contact")


@api_router.post("/send", status_code=status.HTTP_201_CREATED)
async def add_contact_message(payload: ContactBase, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:
        result = await add_contact(db, payload.model_dump(mode="json"), background_tasks)
        return success(result, code=201)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding contact message: {str(e)}")
        raise HTTPException(status_code=500, detail="Error adding contact message")


@api_router.put("/{contact_id}")
async def _update_contact(contact_id: str, payload: ContactMessageUpdate, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:
        data_to_update = {k: v for k, v in payload.model_dump(mode="json").items() if v is not None}
        result = await update_contact(db, contact_id, data_to_update, background_tasks)
        return success(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating contact: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating contact")


@api_router.delete("/{contact_id}")
async def _delete_contact(contact_id: str, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:
        result = await delete_contact(db, contact_id, background_tasks)
        return success(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting contact: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting contact")
