from fastapi import APIRouter
from app.routers.admin.overview import api_router as overview_router
from app.routers.admin.security import api_router as security_router
from app.routers.admin.users import api_router as users_router
from app.routers.admin.outreach import api_router as outreach_router
from app.routers.admin.proposals import api_router as proposals_router
from app.routers.admin.events import api_router as events_router
from app.routers.admin.registrations import api_router as registrations_router
from app.routers.admin.speakers import api_router as speakers_router
from app.routers.sessions import router as sessions_router
from app.routers.admin.sponsor_packages import api_router as sponsor_packages_router

admin_router = APIRouter(prefix="/admin")
admin_router.include_router(overview_router)
admin_router.include_router(security_router)
admin_router.include_router(users_router)
admin_router.include_router(outreach_router)
admin_router.include_router(proposals_router)
admin_router.include_router(events_router)
admin_router.include_router(registrations_router)
admin_router.include_router(speakers_router)
admin_router.include_router(sessions_router)
admin_router.include_router(sponsor_packages_router)
