from uuid import uuid4

from app.database.orm import select, insert, update, delete
from fastapi import BackgroundTasks, HTTPException
from app.schemas.models import ProposalCreate, ProposalDraft, ProposalUpdate, ProposalSummary, ResumeDraft, SubmissionStatus
from app.core.settings import logger
from app.utils.helpers import hash_password, remove_null_values, verify_password


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
        event_code = event_code.strip().upper()
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
        event_code = event_code.strip().upper()
        proposal_data = proposal.model_dump(mode="json")
        if not proposal_data.get("agreed_to_code_of_conduct") or not proposal_data.get("agreed_to_privacy_policy"):
            raise HTTPException(
                status_code=400, detail="You must agree to the code of conduct and privacy policy to submit a proposal")
        if not proposal_data.get("shared_with_sponsors"):
            proposal_data["shared_with_sponsors"] = False
        # TODO : Check cfp deadline for the event and reject proposal if the deadline has passed can be done here
        event_data = await select(db, "events", filter={"code": event_code})
        if not event_data:
            # background task to send email to admin about missing event can be added here
            # TODO: Log the error can be done here
            raise HTTPException(status_code=404, detail="Event not found")
        event_id = event_data[0]["id"]
        existing_proposal = await select(db, "proposals", filter={
            "title": proposal_data["title"], "full_name": proposal_data["full_name"], "email": proposal_data["email"], "event_id": event_id})
        if existing_proposal:
            # background task to send email to admin about duplicate proposal can be added here
            # TODO: Log the error can be done here
            raise HTTPException(
                status_code=400, detail="Proposal with this title already exists for the specified event")
        proposal_data.update(
            {
                "id": str(uuid4()),
                "event_id": event_id,
                "status": SubmissionStatus.SUBMITTED.value
            }
        )
        background_tasks.add_task(insert, db, "proposals", proposal_data)
        # TODO: send email to speaker about successful submission can be done here

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
        # TODO: Check cfp deadline for the event and reject update if the deadline has passed can be done here
        proposal_data = remove_null_values(
            proposal_update.model_dump(mode="json"))
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


async def save_draft(db, draft: ProposalDraft, event_code: str, background_tasks: BackgroundTasks):
    """
    Save a proposal draft to the database.
    """
    try:
        event_code = event_code.strip().upper()
        draft_data = draft.model_dump(mode="json")
        hashed_password = hash_password(draft_data["password_hash"])
        draft_data["password_hash"] = hashed_password
        event_data = await select(db, "events", filter={"code": event_code})
        if not event_data:
            raise HTTPException(status_code=404, detail="Event not found")
        event_id = event_data[0]["id"]
        check_existing_draft = await select(db, "draft_proposals", filter={"email": draft_data["email"], "event_id": event_id})
        if check_existing_draft:
            # TODO: send email to speaker about successful update of the draft can be done here
            background_tasks.add_task(update, db, "draft_proposals", draft_data,
                                      filter={"email": draft_data["email"], "event_id": event_id})
            return {"message": "Proposal draft updated successfully"}
        draft_data.update({
            "id": str(uuid4()),
            "event_id": event_id,
        })
        # background_tasks.add_task(insert, db, "draft_proposals", draft_data)
        await insert(db, "draft_proposals", draft_data)
        return {"message": "Proposal draft saved successfully"}
    except Exception as e:
        logger.error(f"Error saving proposal draft: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


async def resume_draft(db, resumeDraft: ResumeDraft, event_code: str):
    """
    Resume a proposal draft from the database.
    """
    try:
        # TODO: Check cfp deadline for the event and reject resume if the deadline has passed can be done here
        event_code = event_code.strip().upper()

        email = resumeDraft.email
        password = resumeDraft.password
        event_data = await select(db, "events", filter={"code": event_code})
        if not event_data:
            raise HTTPException(status_code=404, detail="Event not found")
        event_id = event_data[0]["id"]
        existing_draft = await select(db, "draft_proposals", filter={"email": email, "event_id": event_id})
        if not existing_draft:
            raise HTTPException(
                status_code=404, detail="Proposal draft not found")
        draft = existing_draft[0]
        if not verify_password(password, draft["password_hash"]):
            raise HTTPException(
                status_code=401, detail="email  or password is incorrect")
        return {"proposal_data": draft["proposal_data"]}
    except Exception as e:
        logger.error(f"Error resuming proposal draft: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")
