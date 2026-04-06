from app.database.orm import select, insert, update, select_with_join, delete
from uuid import uuid4
from fastapi import BackgroundTasks, HTTPException, status
from app.utils.helpers import remove_null_values
from app.core.settings import logger
from app.utils.helpers import remove_null_values


async def add_sponsor_partner(db, payload: dict, event_code: str, background_tasks: BackgroundTasks):
    try:
        existing = await select_with_join(
            db,
            table="sponsors_partners",
            join_table="events",
            join_condition="sponsors_partners.event_id = events.id",
            filter={"events.code": event_code,
                    "sponsors_partners.name": payload["name"]},
        )

        if existing:
            # TODO: sent email to admin about duplicate request
            logger.warning(
                "Sponsor/Partner with name %s already exists for event code %s", payload['name'], event_code)
            return {
                "message": f"Company {payload['name']} partnership/sponsorship request received successfully and is being processed"
            }
        event = await select(db, "events", filter={"code": event_code})
        if not event:
            # TODO: send email to admin about invalid event code
            logger.warning(
                "Event with code %s not found for sponsor/partner inquiry", event_code)
            return {
                "message": f"Event with code {event_code} not found"
            }

        payload.update({
            "id": str(uuid4()),
            "event_id": event[0]["id"],
        })
        background_tasks.add_task(
            insert, db, "sponsors_partners", payload)
        return {"message": f"Company {payload['name']} partnership/sponsorship request received successfully and is being processed"}
    except Exception as e:
        # TODO:  send email to admin about error during processing the request
        logger.error("Error adding sponsor/partner: %s", str(e))
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error adding sponsor/partner")


async def _update_partner_sponsor(db, partner_id: str, payload: dict, background_tasks: BackgroundTasks):
    try:
        existing = await select(db, "sponsors_partners", filter={"id": partner_id})
        payload = remove_null_values(payload)
        if not existing:
            logger.warning(
                "Sponsor/Partner with id %s not found for update", partner_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Sponsor/Partner not found")

        background_tasks.add_task(
            update, db, "sponsors_partners", payload, filter={"id": partner_id})
        return {"message": "Partner/Sponsor updated successfully"}

    except Exception as e:
        # TODO:  send email to admin about error during processing the request
        logger.error("Error updating sponsor/partner: %s", str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error updating sponsor/partner")


async def get_sponsors_partners_by_event(db, event_code: str):
    try:
        partners = await select_with_join(
            db,
            table="sponsors_partners",
            join_table="events",
            join_condition="sponsors_partners.event_id = events.id",
            filter={"events.code": event_code},
        )
        if not partners:
            logger.warning(
                "No sponsors/partners found for event code %s", event_code)

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"No sponsors/partners found for event code {event_code}")
        return partners
    except Exception as e:
        logger.error("Error fetching sponsors/partners: %s", str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error fetching sponsors/partners")


async def get_sponsors_partners(db):
    try:
        partners = await select(db, "sponsors_partners")
        if not partners:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No sponsors/partners found")
        return partners
    except Exception as e:
        logger.error("Error fetching sponsors/partners: %s", str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error fetching sponsors/partners")


async def delete_sponsor_partner(db, partner_id: str, background_tasks: BackgroundTasks):
    try:
        existing = await select(db, "sponsors_partners", filter={"id": partner_id})
        if not existing:
            logger.warning(
                "Sponsor/Partner with id %s not found for deletion", partner_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Sponsor/Partner not found")
        background_tasks.add_task(
            delete, db, "sponsors_partners", filter={"id": partner_id})
        return {"message": "Partner/Sponsor deleted successfully"}

    except Exception as e:
        logger.error("Error deleting sponsor/partner: %s", str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error deleting sponsor/partner")
