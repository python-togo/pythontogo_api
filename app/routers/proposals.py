from fastapi import APIRouter, BackgroundTasks, Depends, status, HTTPException
from app.database.connection import get_db_connection
from app.utils.proposals import (add_proposal, get_proposals_by_event,
                                 get_proposal_by_id, get_all_proposals, update_proposal, delete_proposal)
from app.schemas.models import (
    MessageResponse,
    ProposalCreate,
    ProposalSummary,
    ProposalUpdate

)
from app.core.settings import logger


api_router = APIRouter(prefix="/proposals", tags=["proposals"])


@api_router.post("/create/{event_code}", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_proposal(proposal: ProposalCreate, event_code: str, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    """
    Create a new proposal for an event.
    """
    try:
        event_code = event_code.upper()
        result = await add_proposal(db, proposal, event_code, background_tasks=background_tasks)
        return result
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.get("/list/{event_code}", response_model=list[ProposalSummary])
async def list_proposals(event_code: str, db=Depends(get_db_connection)):
    """
    List all proposals for a specific event.
    """
    try:
        event_code = event_code.upper()
        proposals = await get_proposals_by_event(db, event_code)
        if not proposals:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No proposals found for this event")
        return proposals
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error retrieving proposals: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.get("/list", response_model=list[ProposalSummary])
async def list_all_proposals(db=Depends(get_db_connection)):
    """
    List all proposals across all events.
    """
    try:
        proposals = await get_all_proposals(db)
        if not proposals:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No proposals found")
        return proposals
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.get("/{proposal_id}", response_model=ProposalSummary)
async def get_proposal(proposal_id: str, db=Depends(get_db_connection)):
    """
    Retrieve a proposal by its ID.
    """
    try:
        proposal = await get_proposal_by_id(db, proposal_id)
        if not proposal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Proposal with id {proposal_id} not found")
        return proposal
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.put("/update/{proposal_id}", response_model=MessageResponse)
async def update_proposal_details(proposal_id: str, proposal_update: ProposalUpdate, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    """
    Update a proposal's details.
    """
    try:
        result = await update_proposal(db, proposal_id, proposal_update, background_tasks)
        return result
    except Exception as e:
        logger.error(f"Error updating proposal: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.delete("/delete/{proposal_id}", response_model=MessageResponse)
async def delete_proposal_by_id(proposal_id: str, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    """
    Delete a proposal by its ID.
    """
    try:
        result = await delete_proposal(db, proposal_id, background_tasks)
        return result
    except Exception as e:

        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")
