from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from app.database.connection import get_db_connection
<<<<<<< HEAD
from app.utils.proposals import add_proposal, get_proposal_by_id, update_proposal, delete_proposal
from app.schemas.models import ProposalCreate, ProposalUpdate
from app.core.settings import logger
from app.utils.responses import success
from app.utils.pagination import paginate
=======
from app.utils.proposals import (add_proposal, get_proposals_by_event,
                                 get_proposal_by_id, get_all_proposals, update_proposal, delete_proposal, save_draft, resume_draft)
from app.schemas.models import (
    MessageResponse,
    ProposalCreate,
    ProposalDraft,
    ProposalSummary,
    ProposalUpdate,
    ResumeDraft,
    ResumeDraftResponse

)
from app.core.settings import logger
from app.utils.helpers import verify_password, hash_password

>>>>>>> origin/main

api_router = APIRouter(prefix="/proposals", tags=["proposals"])


<<<<<<< HEAD
@api_router.post("/create/{event_code}", status_code=status.HTTP_201_CREATED)
=======
@api_router.post("/save-draft/{event_code}", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def save_proposal_draft(draftProposal: ProposalDraft, event_code: str, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    """Save a proposal draft for an event.
    """
    try:
        event_code = event_code.strip().upper()
        result = await save_draft(db, draftProposal, event_code, background_tasks)
        return result
    except Exception as e:
        logger.error(f"Error saving proposal draft: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.post("/resume-draft/{event_code}", response_model=ResumeDraftResponse)
async def resume_proposal_draft(resumeDraft: ResumeDraft, event_code: str, db=Depends(get_db_connection)):
    """Resume a saved proposal draft by providing email, password, and event code.
    """
    try:
        result = await resume_draft(db, resumeDraft, event_code)
        return result
    except Exception as e:
        logger.error(f"Error resuming proposal draft: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.post("/create/{event_code}", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
>>>>>>> origin/main
async def create_proposal(proposal: ProposalCreate, event_code: str, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:
        result = await add_proposal(db, proposal, event_code.strip().upper(), background_tasks=background_tasks)
        return success(result, code=201)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.get("/list/{event_code}")
async def list_proposals(
    event_code: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
):
    try:
        rows, total = await paginate(
            db,
            """
            SELECT p.*
            FROM proposals p
            JOIN events e ON p.event_id = e.id
            WHERE e.code = %s
            ORDER BY p.created_at DESC
            """,
            (event_code.strip().upper(),),
            page, per_page,
        )
        if not rows and page == 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No proposals found for this event")
        return success(rows, total=total, page=page, per_page=per_page)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving proposals: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.get("/list")
async def list_all_proposals(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
):
    try:
        rows, total = await paginate(
            db,
            "SELECT * FROM proposals ORDER BY created_at DESC",
            (),
            page, per_page,
        )
        if not rows and page == 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No proposals found")
        return success(rows, total=total, page=page, per_page=per_page)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.get("/{proposal_id}")
async def get_proposal(proposal_id: str, db=Depends(get_db_connection)):
    try:
        proposal = await get_proposal_by_id(db, proposal_id)
        if not proposal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Proposal with id {proposal_id} not found")
        return success(proposal)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.put("/update/{proposal_id}")
async def update_proposal_details(proposal_id: str, proposal_update: ProposalUpdate, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:
        result = await update_proposal(db, proposal_id, proposal_update, background_tasks)
        return success(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating proposal: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.delete("/delete/{proposal_id}")
async def delete_proposal_by_id(proposal_id: str, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:
        result = await delete_proposal(db, proposal_id, background_tasks)
        return success(result)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")
