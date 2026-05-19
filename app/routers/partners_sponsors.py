<<<<<<< HEAD
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
=======
from fastapi import APIRouter, BackgroundTasks, Depends, status, HTTPException
from app.utils.sponsor_partner import (add_sponsor_partner, get_confirmed_sponsors_partners, get_confirmed_sponsors_partners_by_event, get_sponsors_partners_by_event,
                                       get_sponsors_partners, _update_partner_sponsor, delete_sponsor_partner)
>>>>>>> origin/main

from app.utils.sponsor_partner import add_sponsor_partner, _update_partner_sponsor, delete_sponsor_partner
from app.schemas.models import PartnerSponsorUpdate, PartnershipSponsorshipInquiry
from app.database.connection import get_db_connection
from app.core.settings import logger
from app.utils.responses import success
from app.utils.pagination import paginate

api_router = APIRouter(prefix="/partners-sponsors", tags=["Partners & Sponsors"])


@api_router.post("/inquiry/{event_code}", status_code=status.HTTP_202_ACCEPTED)
async def partnership_sponsorship_inquiry(
    event_code: str,
    payload: PartnershipSponsorshipInquiry,
    background_tasks: BackgroundTasks,
    db=Depends(get_db_connection),
):
    try:
        result = await add_sponsor_partner(db, payload.model_dump(mode="json"), event_code.strip().upper(), background_tasks)
        return success(result, code=202)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing partnership/sponsorship inquiry: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing partnership/sponsorship request: {str(e)}")


@api_router.get("/all")
async def get_all_partners_sponsors(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
):
    try:
        rows, total = await paginate(
            db,
            "SELECT * FROM sponsors_partners ORDER BY created_at DESC",
            (),
            page, per_page,
        )
        if not rows and page == 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No partners/sponsors found")
        return success(rows, total=total, page=page, per_page=per_page)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving partners/sponsors: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving partners/sponsors")


<<<<<<< HEAD
@api_router.get("/all/{event_code}")
async def get_partners_sponsors(
    event_code: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
):
=======
@api_router.get("/confirmed/all", response_model=list[PartnerSponsorSummary])
async def get_confirmed_partners_sponsors(db=Depends(get_db_connection)):
    try:
        partners_sponsors = await get_confirmed_sponsors_partners(db)
        if not partners_sponsors:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No partners/sponsors found")

        return partners_sponsors
    except Exception as e:
        logger.error(f"Error retrieving partners/sponsors: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail="Error retrieving partners/sponsors")


@api_router.get("/all/{event_code}", response_model=list[PartnerSponsorSummary])
async def get_partners_sponsors(event_code: str, db=Depends(get_db_connection)):
>>>>>>> origin/main
    try:
        code = event_code.strip().upper()
        rows, total = await paginate(
            db,
            """
            SELECT sp.*
            FROM sponsors_partners sp
            JOIN events e ON sp.event_id = e.id
            WHERE e.code = %s
            ORDER BY sp.created_at DESC
            """,
            (code,),
            page, per_page,
        )
        if not rows and page == 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No partners/sponsors found for event {event_code}")
        return success(rows, total=total, page=page, per_page=per_page)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving partners/sponsors for event {event_code}: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail="Error retrieving partners/sponsors")


@api_router.get("/confirmed/all/{event_code}", response_model=list[PartnerSponsorSummary])
async def get_confirmed_partners_sponsors(event_code: str, db=Depends(get_db_connection)):
    try:
        event_code = event_code.strip().upper()
        partners_sponsors = await get_confirmed_sponsors_partners_by_event(db, event_code=event_code)
        if not partners_sponsors:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"No partners/sponsors found for event {event_code}")
        return partners_sponsors
    except Exception as e:
        logger.error(f"Error retrieving partners/sponsors: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving partners/sponsors")


@api_router.put("/{partner_id}")
async def update_partner_sponsor(
    partner_id: str,
    payload: PartnerSponsorUpdate,
    background_tasks: BackgroundTasks,
    db=Depends(get_db_connection),
):
    try:
        result = await _update_partner_sponsor(db, partner_id, payload.model_dump(mode="json"), background_tasks)
        return success(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating partner/sponsor: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating partner/sponsor")


@api_router.delete("/{partner_id}")
async def delete_partner_sponsor(partner_id: str, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:
        result = await delete_sponsor_partner(db, partner_id=partner_id, background_tasks=background_tasks)
        return success(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting partner/sponsor: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting partner/sponsor")
