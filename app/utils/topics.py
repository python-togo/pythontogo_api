from app.database.orm import select, insert, update, delete, select_with_join
from app.schemas.models import TopicCreate, TopicUpdate
from fastapi import BackgroundTasks, HTTPException
from uuid import uuid4
from app.utils import topics
from app.utils.helpers import remove_null_values
from app.core.settings import logger


async def get_all_topics(db):
    """
    Retrieve all topics from the database.
    """
    try:
        topics = await select(db, "topics")
        if not topics:
            raise HTTPException(status_code=404, detail="No topics found")
        return topics
    except Exception as e:
        logger.error(f"Error retrieving topics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error: ")


async def get_topics_by_event(db, event_code):
    """
    Retrieve all topics for a specific event.
    """
    try:
        event_code = event_code.strip().upper()
        topics = await select_with_join(db, table="topics", join_table="events",
                                        join_condition="topics.event_id = events.id",
                                        columns=["topics.id", "topics.name_fr", "topics.name_en",
                                                 "topics.description_fr", "topics.description_en",
                                                 "topics.event_id", "topics.created_at", "topics.updated_at"],
                                        filter={"events.code": event_code})

        if not topics:
            raise HTTPException(
                status_code=404, detail="No topics found for the specified event or event does not exist")
        return topics
    except Exception as e:
        logger.error(f"Error retrieving topics: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error: ")


async def get_topic_by_id(db, topic_id):
    """
    Retrieve a topic by its ID.
    """
    try:
        topic = await select(db, "topics", filter={"id": topic_id})
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        return topic[0]
    except Exception as e:
        logger.error(f"Error retrieving topic: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


async def add_topic(db, topic: TopicCreate, event_code: str, background_tasks: BackgroundTasks):
    """
    Add a new topics to the database.
    """
    try:
        event_code = event_code.strip().upper()
        topics_data = topic.model_dump(mode="json")
        event_data = await select(db, "events", filter={"code": event_code})
        if not event_data:
            raise HTTPException(status_code=404, detail="Event not found")
        event_id = event_data[0]["id"]
        existing_topics = await select(db, "topics", filter={
            "name_fr": topics_data["name_fr"], "event_id": event_id, "name_en": topics_data["name_en"]})
        if existing_topics:
            raise HTTPException(
                status_code=400, detail="topics already exists for this event")

        topics_data.update({
            "id": str(uuid4()),
            "event_id": event_id,
        })
        background_tasks.add_task(insert, db, "topics", topics_data)

        return {"message": "topics created successfully"}
    except Exception as e:
        logger.error(f"Error adding topics: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


async def update_topic(db, topic_id, topic: TopicUpdate, background_tasks: BackgroundTasks):
    """
    Update an existing topics in the database.
    """
    try:
        topics_data = remove_null_values(topic.model_dump(mode="json"))
        existing_topics = await select(db, "topics", filter={"id": topic_id})
        if not existing_topics:
            raise HTTPException(status_code=404, detail="topics not found")

        background_tasks.add_task(update, db, "topics", topics_data,
                                  filter={"id": topic_id})
        return {"message": "topics updated successfully"}
    except Exception as e:
        logger.error(f"Error updating topics: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


async def delete_topic(db, topic_id, background_tasks: BackgroundTasks):
    """
    Delete a topics from the database.
    """
    try:
        existing_topics = await select(db, "topics", filter={"id": topic_id})
        if not existing_topics:
            raise HTTPException(status_code=404, detail="topics not found")

        background_tasks.add_task(
            delete, db, "topics", filter={"id": topic_id})
        return {"message": "topics deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting topics: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")
