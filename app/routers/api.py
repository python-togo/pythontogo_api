from fastapi import APIRouter
from app.schemas.models import (
    AttendeeRegistrationCreate,
    ContactMessageCreate,
    HealthResponse,
    MessageResponse,
    PartnershipInquiryCreate,
    PartnerType,
    SessionSummary,
    SessionType,
    SponsorInquiryCreate,
    SponsorSummary,
    TalkSubmissionCreate,
    TicketSummary,
    VenueSummary,
    WorkshopSubmissionCreate,
    YearAttendeesResponse,
    YearScheduleResponse,
    YearSpeakersResponse,
    YearSponsorsResponse,
    YearTicketsResponse,
    YearVenuesResponse,
    YearWorkshopsResponse,
)

api_router = APIRouter(prefix="/api/v2", tags=["v2.1.0"])


@api_router.get("/sponsers/{edition_year}")
async def get_sponsers(edition_year: int) -> YearSponsorsResponse:
    return YearSponsorsResponse(edition_year=edition_year, items=[])


@api_router.get("/schedule/{edition_year}", response_model=YearScheduleResponse)
async def get_schedule(edition_year: int) -> YearScheduleResponse:
    return YearScheduleResponse(
        edition_year=edition_year,
        items=[
            SessionSummary(
                title="Opening Keynote",
                session_type=SessionType.KEYNOTE,
            )
        ],
    )


@api_router.get("/speakers/{edition_year}", response_model=YearSpeakersResponse)
async def get_speakers(edition_year: int) -> YearSpeakersResponse:
    return YearSpeakersResponse(edition_year=edition_year, items=[])


@api_router.get("/attendees/{edition_year}", response_model=YearAttendeesResponse)
async def get_attendees(edition_year: int) -> YearAttendeesResponse:
    return YearAttendeesResponse(edition_year=edition_year, items=[])


@api_router.get("/venues/{edition_year}", response_model=YearVenuesResponse)
async def get_venues(edition_year: int) -> YearVenuesResponse:
    return YearVenuesResponse(
        edition_year=edition_year,
        items=[VenueSummary(name="Main Venue")],
    )


@api_router.get("/tickets/{edition_year}", response_model=YearTicketsResponse)
async def get_tickets(edition_year: int) -> YearTicketsResponse:
    return YearTicketsResponse(
        edition_year=edition_year,
        items=[TicketSummary(name="Standard", price="0",
                             currency="USD", is_active=True)],
    )


@api_router.get("/workshops/{edition_year}", response_model=YearWorkshopsResponse)
async def get_workshops(edition_year: int) -> YearWorkshopsResponse:
    return YearWorkshopsResponse(edition_year=edition_year, items=[])


@api_router.get("/sponsors/{edition_year}", response_model=YearSponsorsResponse)
async def get_sponsors(edition_year: int) -> YearSponsorsResponse:
    return YearSponsorsResponse(
        edition_year=edition_year,
        items=[
            SponsorSummary(
                name="Python Software Foundation",
                partner_type=PartnerType.SPONSORSHIP,
                is_confirmed=True,
            )
        ],
    )


@api_router.post("/contact", response_model=MessageResponse)
async def get_contact(payload: ContactMessageCreate) -> MessageResponse:
    return MessageResponse(
        message=f"Contact message from {payload.name} received successfully"
    )


@api_router.post("/register", response_model=MessageResponse)
async def register_attendee(payload: AttendeeRegistrationCreate) -> MessageResponse:
    return MessageResponse(
        message=f"Attendee {payload.full_name} with email {payload.email} registered successfully"
    )


@api_router.post("/submit-talk", response_model=MessageResponse)
async def submit_talk(payload: TalkSubmissionCreate) -> MessageResponse:
    return MessageResponse(message=f"Talk '{payload.title}' submitted successfully")


@api_router.post("/submit-workshop", response_model=MessageResponse)
async def submit_workshop(payload: WorkshopSubmissionCreate) -> MessageResponse:
    return MessageResponse(message=f"Workshop '{payload.title}' submitted successfully")


@api_router.post("/sponsor", response_model=MessageResponse)
async def sponsor_event(payload: SponsorInquiryCreate) -> MessageResponse:
    tier = payload.tier.value if payload.tier else "custom"
    return MessageResponse(
        message=f"Company {payload.name} sponsorship request ({tier}) received successfully"
    )


@api_router.post("/partnership", response_model=MessageResponse)
async def partnership(payload: PartnershipInquiryCreate) -> MessageResponse:
    return MessageResponse(
        message=f"Company {payload.name} partnership request received successfully"
    )


@api_router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="healthy")
