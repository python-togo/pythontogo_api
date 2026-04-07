from app.database.orm import select, insert, update, delete, select_with_join
from app.schemas.models import TrackCreate, TrackUpdate
from fastapi import BackgroundTasks, HTTPException
from uuid import uuid4
from app.utils.helpers import remove_null_values
from app.core.settings import logger


async def get_all_tracks(db):
    """
    Retrieve all tracks from the database.
    """
    try:
        tracks = await select(db, "tracks")
        if not tracks:
            raise HTTPException(status_code=404, detail="No tracks found")
        return tracks
    except Exception as e:
        logger.error(f"Error retrieving tracks: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error: ")


async def get_tracks_by_event(db, event_code):
    """
    Retrieve all tracks for a specific event.
    """
    try:
        event_code = event_code.strip().upper()
        tracks = await select_with_join(db, table="tracks", join_table="events",
                                        join_condition="tracks.event_id = events.id", filter={"events.code": event_code})
        logger.info(f"Retrieved tracks for event {event_code}: {tracks}")
        if not tracks:
            raise HTTPException(
                status_code=404, detail="No tracks found for the specified event or event does not exist")
        return tracks
    except Exception as e:
        logger.error(f"Error retrieving tracks: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error: ")


async def get_track_by_id(db, track_id):
    """
    Retrieve a track by its ID.
    """
    try:
        track = await select(db, "tracks", filter={"id": track_id})
        if not track:
            raise HTTPException(status_code=404, detail="Track not found")
        return track[0]
    except Exception as e:
        logger.error(f"Error retrieving track: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def add_track(db, track: TrackCreate, event_code: str, background_tasks: BackgroundTasks):
    """
    Add a new track to the database.
    """
    try:
        event_code = event_code.strip().upper()
        track_data = track.model_dump(mode="json")
        event_data = await select(db, "events", filter={"code": event_code})
        if not event_data:
            raise HTTPException(status_code=404, detail="Event not found")
        event_id = event_data[0]["id"]
        existing_track = await select(db, "tracks", filter={
            "name": track_data["name"], "event_id": event_id})
        if existing_track:
            raise HTTPException(
                status_code=400, detail="Track with the same name already exists for this event")

        track_data.update({
            "id": str(uuid4()),
            "event_id": event_id,
        })
        background_tasks.add_task(insert, db, "tracks", track_data)

        return {"message": "Track created successfully"}
    except Exception as e:
        logger.error(f"Error adding track: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def update_track(db, track_id, track: TrackUpdate, background_tasks: BackgroundTasks):
    """
    Update an existing track in the database.
    """
    try:
        track_data = remove_null_values(track.model_dump(mode="json"))
        existing_track = await select(db, "tracks", filter={"id": track_id})
        if not existing_track:
            raise HTTPException(status_code=404, detail="Track not found")

        background_tasks.add_task(update, db, "tracks", track_data,
                                  filter={"id": track_id})
        return {"message": "Track updated successfully"}
    except Exception as e:
        logger.error(f"Error updating track: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def delete_track(db, track_id, background_tasks: BackgroundTasks):
    """
    Delete a track from the database.
    """
    try:
        existing_track = await select(db, "tracks", filter={"id": track_id})
        if not existing_track:
            raise HTTPException(status_code=404, detail="Track not found")

        background_tasks.add_task(
            delete, db, "tracks", filter={"id": track_id})
        return {"message": "Track deleted successfully"}
    except Exception as e:
        # TODO: Log the exception details for debugging
        raise HTTPException(status_code=500, detail="Internal server error")
