from fastapi.params import Depends

from app.routers.contacts import api_router as contacts_router
from app.routers.partners_sponsors import api_router as partners_sponsors_router
from app.routers.events import api_router as events_router
from app.routers.proposals import api_router as proposals_router
from app.routers.tracks import api_router as tracks_router
from app.routers.topics import api_router as topics_router
from app.routers.proposal_formats import api_router as proposal_formats_router
from app.routers.speaker import api_router as speakers_router
from app.routers.checkout import api_router as checkout_router
from app.routers.tickets import api_router as tickets_router
from app.routers.registrations import api_router as registrations_router
from app.routers.job_offers import api_router as job_offers_router
from app.routers.sessions import api_router as sessions_router
from app.routers.vauchers import api_router as vauchers_router
from app.routers.teams import api_router as teams_router
from app.routers.access_grant import api_router as access_grant_router
from app.routers.feedbacks import api_router as feedbacks_router
from fastapi import APIRouter
from app.core.security import verify_api_key


api_routers = APIRouter(
    prefix="/api/v2", tags=["v2.1.0"], dependencies=[Depends(verify_api_key)])


api_routers.include_router(partners_sponsors_router)
api_routers.include_router(contacts_router)
api_routers.include_router(events_router)
api_routers.include_router(proposals_router)
api_routers.include_router(tracks_router)
api_routers.include_router(topics_router)
api_routers.include_router(proposal_formats_router)
api_routers.include_router(speakers_router)
api_routers.include_router(checkout_router)
api_routers.include_router(registrations_router)
api_routers.include_router(tickets_router)
api_routers.include_router(job_offers_router)
api_routers.include_router(sessions_router)
api_routers.include_router(vauchers_router)
api_routers.include_router(teams_router)
api_routers.include_router(access_grant_router)
api_routers.include_router(feedbacks_router)
