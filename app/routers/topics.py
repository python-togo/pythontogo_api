from app.utils.topics import (add_topic, get_topics_by_event,
                              get_topic_by_id, get_all_topics)
from app.schemas.models import (
    MessageResponse,
    TopicCreate,
    TopicSummary,
    TopicUpdate,
)
from app.core.settings import logger
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from app.database.connection import get_db_connection


api_router = APIRouter(prefix="/topics", tags=["topics"])


@api_router.post("/create/{event_code}", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_topic(topic: TopicCreate, event_code: str, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    """
    Create a new topic for an event.
    """
    try:
        result = await add_topic(db, topic, event_code, background_tasks)
        return result
    except Exception as e:
        logger.error(f"Error creating topic: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.get("/list/{event_code}", response_model=list[TopicSummary])
async def list_topics(event_code: str, db=Depends(get_db_connection)):
    """
    List all topics for a specific event.
    """
    try:
        topics = await get_topics_by_event(db, event_code)
        if not topics:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No topics found for this event")
        return topics
    except Exception as e:
        logger.error(f"Error retrieving topics: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.get("/list", response_model=list[TopicSummary])
async def list_all_topics(db=Depends(get_db_connection)):
    """
    List all topics across all events.
    """
    try:
        topics = await get_all_topics(db)
        if not topics:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No topics found")
        return topics
    except Exception as e:
        logger.error(f"Error retrieving topics: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.get("/{topic_id}", response_model=TopicSummary)
async def get_topic(topic_id: str, db=Depends(get_db_connection)):
    """
    Get a topic by its ID.
    """
    try:
        topic = await get_topic_by_id(db, topic_id)
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Topic not found")
        return topic
    except Exception as e:
        logger.error(f"Error retrieving topic: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.put("/update/{topic_id}", response_model=MessageResponse)
async def update_topic(topic_id: str, topic: TopicUpdate, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    """
    Update an existing topic.
    """
    try:
        # Implementation for updating a topic would go here
        return {"message": "Topic updated successfully"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.delete("/delete/{topic_id}", response_model=MessageResponse)
async def delete_topic(topic_id: str, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    """
    Delete a topic by its ID.
    """
    try:
        # Implementation for deleting a topic would go here
        return {"message": "Topic deleted successfully"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")
