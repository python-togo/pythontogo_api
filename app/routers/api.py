from fastapi.params import Depends

from app.routers.contacts import api_router as contacts_router
from app.routers.partners_sponsors import api_router as partners_sponsors_router
from app.routers.events import api_router as events_router
from app.routers.proposals import api_router as proposals_router
from app.routers.tracks import api_router as tracks_router
from fastapi import APIRouter
from app.core.security import verify_api_key


api_routers = APIRouter(
    prefix="/api/v2", tags=["v2.1.0"], dependencies=[Depends(verify_api_key)])


api_routers.include_router(partners_sponsors_router)
api_routers.include_router(contacts_router)
api_routers.include_router(events_router)
api_routers.include_router(proposals_router)
api_routers.include_router(tracks_router)
