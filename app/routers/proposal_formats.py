from app.utils.proposal_formats import get_all_formats, get_formats_by_event, get_format_by_id, add_format, update_format, delete_format
from app.schemas.models import (
    MessageResponse,
    ProposalFormatCreate,
    ProposalFormatSummary,
    ProposalFormatUpdate,
)
from app.core.settings import logger
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from app.database.connection import get_db_connection

api_router = APIRouter(prefix="/proposal-formats", tags=["proposal-formats"])


@api_router.post("/create/{event_code}", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_format(format: ProposalFormatCreate, event_code: str, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    """
    Create a new format for an event.
    """
    try:

        result = await add_format(db, format, event_code, background_tasks)
        return result
    except Exception as e:
        logger.error(f"Error creating format: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.get("/list/{event_code}", response_model=list[ProposalFormatSummary])
async def list_formats(event_code: str, db=Depends(get_db_connection)):
    """
    List all formats for a specific event.
    """
    try:
        formats = await get_formats_by_event(db, event_code)
        if not formats:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No formats found for this event")
        return formats
    except Exception as e:
        logger.error(f"Error retrieving formats: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")
