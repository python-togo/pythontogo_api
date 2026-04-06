from fastapi import APIRouter, BackgroundTasks, Depends, status, HTTPException
from app.utils.sponsor_partner import (add_sponsor_partner, get_sponsors_partners_by_event,
                                       get_sponsors_partners, _update_partner_sponsor, delete_sponsor_partner)


from app.schemas.models import (
    HealthResponse,
    MessageResponse,
    PartnerSponsorSummary,
    PartnerSponsorUpdate,

    PartnershipSponsorshipInquiry,
    SponsorsPartnersList,


)
from app.database.connection import get_db_connection
from app.core.settings import logger

api_router = APIRouter(prefix="/partners-sponsors",
                       tags=["Partners & Sponsors"])


@api_router.post("/inquiry/{event_code}", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED)
async def partnership_sponsorship_inquiry(event_code: str, payload: PartnershipSponsorshipInquiry, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:
        event_code = event_code.upper()
        result = await add_sponsor_partner(db, payload.model_dump(), event_code, background_tasks)
        return result
    except Exception as e:
        logger.error(
            f"Error processing partnership/sponsorship inquiry: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail=f"Error processing partnership/sponsorship request: {str(e)}")


@api_router.get("/all", response_model=list[PartnerSponsorSummary])
async def get_all_partners_sponsors(db=Depends(get_db_connection)):
    try:
        partners_sponsors = await get_sponsors_partners(db)
        if not partners_sponsors:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No partners/sponsors found")

        return partners_sponsors
    except Exception as e:
        logger.error(f"Error retrieving partners/sponsors: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Error retrieving partners/sponsors")


@api_router.get("/all/{event_code}", response_model=list[PartnerSponsorSummary])
async def get_partners_sponsors(event_code: str, db=Depends(get_db_connection)):
    try:
        event_code = event_code.upper()
        partners_sponsors = await get_sponsors_partners_by_event(db, event_code=event_code)
        if not partners_sponsors:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"No partners/sponsors found for event {event_code}")
        return partners_sponsors
    except Exception as e:
        logger.error(f"Error retrieving partners/sponsors: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail="Error retrieving partners/sponsors")


@api_router.put("/{partner_id}", response_model=MessageResponse)
async def update_partner_sponsor(partner_id: str, payload: PartnerSponsorUpdate, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:
        data_to_update = {k: v for k,
                          v in payload.model_dump().items() if v is not None}

        result = await _update_partner_sponsor(db, partner_id, data_to_update, background_tasks)
        return result
    except Exception as e:
        logger.error(f"Error updating partner/sponsor: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail="Error updating partner/sponsor")


@api_router.delete("/{partner_id}", response_model=MessageResponse)
async def delete_partner_sponsor(partner_id: str, background_tasks: BackgroundTasks, db=Depends(get_db_connection)):
    try:
        result = await delete_sponsor_partner(db, partner_id=partner_id, background_tasks=background_tasks)
        return result
    except Exception as e:
        # TODO - logging the error can be done here

        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail="Error deleting partner/sponsor")
