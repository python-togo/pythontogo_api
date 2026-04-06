from uuid import uuid4

from app.database.orm import select, insert, update, delete, select_with_join
from fastapi import BackgroundTasks, HTTPException
from app.schemas.models import ProposalCreate, ProposalUpdate, ProposalSummary
from app.core.settings import logger
from app.utils.helpers import remove_null_values


async def get_all_proposals(db):
    """
    Retrieve all proposals from the database.
    """
    try:
        proposals = await select(db, "proposals")
        if not proposals:
            raise HTTPException(status_code=404, detail="No proposals found")
        return proposals
    except Exception as e:
        # TODO: Log the exception details for debugging
        logger.error(f"Error retrieving proposals: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


async def get_proposals_by_event(db, event_code):
    """
    Retrieve all proposals for a specific event.
    """
    try:
        event_code = event_code.upper()
        event_data = await select(db, "events", filter={"code": event_code})
        if not event_data:
            raise HTTPException(status_code=404, detail="Event not found")

        proposals = await select(db, "proposals", filter={"event_id": event_data[0]["id"]})
        if not proposals:
            raise HTTPException(
                status_code=404, detail="No proposals found for the specified event")
        return proposals
    except Exception as e:
        # TODO: Log the exception details for debugging
        logger.error(f"Error retrieving proposals: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


async def get_proposal_by_id(db, proposal_id):
    """
    Retrieve a proposal by its ID.
    """
    try:
        proposal = await select(db, "proposals", filter={"id": proposal_id})
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        return proposal[0]
    except Exception as e:
        # TODO: Log the exception details for debugging
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


async def add_proposal(db, proposal: ProposalCreate, event_code: str, background_tasks: BackgroundTasks):
    """
    Add a new proposal to the database.
    """
    try:
        event_code = event_code.upper()
        proposal_data = proposal.model_dump()
        event_data = await select(db, "events", filter={"code": event_code})
        if not event_data:
            # background task to send email to admin about missing event can be added here
            # TODO: Log the error can be done here
            raise HTTPException(status_code=404, detail="Event not found")
        event_id = event_data[0]["id"]
        existing_proposal = await select(db, "proposals", filter={
            "title": proposal_data["title"], "event_id": event_id})
        if existing_proposal:
            # background task to send email to admin about duplicate proposal can be added here
            # TODO: Log the error can be done here
            raise HTTPException(
                status_code=400, detail="Proposal with this title already exists for the specified event")
        proposal_data.update(
            {
                "id": str(uuid4()),
                "event_id": event_id
            }
        )
        background_tasks.add_task(insert, db, "proposals", proposal_data)

        return {"message": "Proposal created successfully"}
    except Exception as e:
        # TODO: send email to admin about error during processing the request can be done here
        logger.error(f"Error adding proposal: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


async def update_proposal(db, proposal_id: str, proposal_update: ProposalUpdate, background_tasks: BackgroundTasks):
    """
    Update details of an existing proposal.
    """
    try:
        proposal_data = remove_null_values(proposal_update.model_dump())
        if not proposal_data:
            raise HTTPException(
                status_code=400, detail="No valid fields provided for update")
        existing_proposal = await select(db, "proposals", filter={"id": proposal_id})
        if not existing_proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")

        background_tasks.add_task(update, db, "proposals", proposal_data,
                                  filter={"id": proposal_id})
        return {"message": "Proposal updated successfully"}
    except Exception as e:
        logger.error(f"Error updating proposal: {str(e)}")
        # TODO: send email to admin about error during processing the request can be done here
        raise HTTPException(status_code=500, detail="Internal server error")


async def delete_proposal(db, proposal_id: str, background_tasks: BackgroundTasks):
    """
    Delete a proposal from the database.
    """
    try:
        existing_proposal = await select(db, "proposals", filter={"id": proposal_id})
        if not existing_proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")

        background_tasks.add_task(
            delete, db, "proposals", filter={"id": proposal_id})
        return {"message": "Proposal deleted successfully"}
    except Exception as e:
        # TODO: Log the exception details for debugging
        raise HTTPException(status_code=500, detail="Internal server error")
