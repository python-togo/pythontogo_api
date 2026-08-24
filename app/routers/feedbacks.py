from fastapi import APIRouter, BackgroundTasks, Depends, Request, status, HTTPException

from app.utils.feedback import (
    add_feedback, get_feedback_by_id, get_all_feedbacks, update_feedback, delete_feedback)

from app.schemas.models import (
    FeedbackSummary,
    MessageResponse,
    FeedbackUpdate,
    FeedbackBase,

)
from app.database.connection import get_db_connection
from app.core.settings import logger


api_router = APIRouter(prefix="/feedbacks", tags=["feedbacks"])


@api_router.get("/", response_model=list[FeedbackSummary])
async def _get_all_feedbacks(db=Depends(get_db_connection)):
    try:
        feedbacks = await get_all_feedbacks(db)
        if not feedbacks:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No feedbacks found")
        return feedbacks
    except Exception as e:
        logger.error(f"Error retrieving feedbacks: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail="Error retrieving feedbacks")


@api_router.get("/{feedback_id}", response_model=FeedbackSummary)
async def _get_feedback_by_id(feedback_id: str, db=Depends(get_db_connection)):
    try:
        feedback = await get_feedback_by_id(db, feedback_id)
        if not feedback:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Feedback with id {feedback_id} not found")
        return feedback
    except Exception as e:
        logger.error(
            f"Error retrieving feedback with id {feedback_id}: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail="Error retrieving feedback")


@api_router.post("/send", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_feedback_message(request: Request, payload: FeedbackBase):
    """Add a new feedback."""
    try:
        result = await add_feedback(request.app.state.db_pool, payload.model_dump(mode="json"))
        return result
    except Exception as e:
        logger.error(f"Error adding feedback: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail="Error adding feedback")


@api_router.put("/{feedback_id}", response_model=MessageResponse)
async def _update_feedback(feedback_id: str, payload: FeedbackUpdate, db=Depends(get_db_connection)):
    try:
        data_to_update = {k: v for k,
                          v in payload.model_dump(mode="json").items() if v is not None}

        result = await update_feedback(db, feedback_id, data_to_update)
        return result
    except Exception as e:
        logger.error(f"Error updating feedback: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail="Error updating feedback")


@api_router.delete("/{feedback_id}", response_model=MessageResponse)
async def _delete_feedback(feedback_id: str, db=Depends(get_db_connection)):
    try:
        result = await delete_feedback(db, feedback_id)
        return result
    except Exception as e:
        logger.error(f"Error deleting feedback: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail="Error deleting feedback")
