from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, HttpUrl


class PackageTier(str, Enum):
    HEADLINE = "headline"
    PLATINUM = "platinum"
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"
    HEART = "heart"
    CUSTOM = "custom"


class DeliveryMethod(str, Enum):
    ONSITE = "onsite"
    ONLINE = "online"
    HYBRID = "hybrid"


class HealthResponse(BaseModel):
    status: str


class MessageResponse(BaseModel):
    message: str


# SPONSORS/PARTNERS SCHEMAS


class PartnerType(str, Enum):
    PARTNERSHIP = "partnership"
    SPONSORSHIP = "sponsorship"
    PYTHON_COMMUNITY = "python_community_partner"
    COMMUNITY_PARTNER = "community_partner"
    OTHER = "other"


class SponsorPartnerBase(BaseModel):
    name: str
    website_url: HttpUrl = None
    contact_name: str
    contact_email: EmailStr
    contact_phone: str | None = None
    description: str | None = None
    logo_url: str | None = None
    partner_type: PartnerType


class PartnershipSponsorshipInquiry(SponsorPartnerBase):
    package_tier: PackageTier | None = None


class PartnerSponsorSummary(SponsorPartnerBase):
    id: UUID
    event_id: UUID
    website_url: str = None
    contact_email: str
    package_tier: PackageTier | None = None
    package_id: UUID | None = None
    is_confirmed: bool = False
    created_at: datetime
    updated_at: datetime


class SponsorsPartnersList(BaseModel):
    sponsors_partners: list[PartnerSponsorSummary] = Field(
        default_factory=list)


class PartnerSponsorUpdate(BaseModel):
    name: str | None = None
    website_url: HttpUrl | None = None
    contact_name: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = None
    description: str | None = None
    logo_url: str | None = None
    partner_type: PartnerType | None = None
    package_tier: PackageTier | None = None
    package_id: UUID | None = None
    is_confirmed: bool | None = None


# ── Sponsor packages ──────────────────────────────────────────────────────────

class SponsorPackageCreate(BaseModel):
    name: str
    tier: PackageTier
    description: str | None = None
    price: Decimal = Decimal("0.00")
    benefits: list[str] = Field(default_factory=list)
    max_slots: int | None = None
    is_active: bool = True


class SponsorPackageUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: Decimal | None = None
    benefits: list[str] | None = None
    max_slots: int | None = None
    is_active: bool | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SponsorPackageSummary(BaseModel):
    id: UUID
    event_id: UUID
    name: str
    tier: PackageTier
    description: str | None = None
    price: Decimal
    benefits: list[str]
    max_slots: int | None = None
    slots_used: int = 0
    is_active: bool
    created_at: datetime
    updated_at: datetime
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


# cONTACT MESSAGES SCHEMA

class ContactBase(BaseModel):
    name: str
    email: EmailStr
    subject: str = "General Inquiry"
    message: str


class ContactMessageSummary(ContactBase):
    id: UUID
    email: str
    is_resolved: bool = False
    created_at: datetime
    updated_at: datetime


class ContactMessagesList(BaseModel):
    contact_messages: list[ContactMessageSummary] = Field(
        default_factory=list)


class ContactMessageUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    subject: str | None = None
    message: str | None = None
    is_resolved: bool | None = None
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class UserRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"
    STAFF = "staff"


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserSummary(BaseModel):
    id: UUID
    username: str
    email: str
    full_name: str | None = None
    role: UserRole
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: str | None = None
    email: str | None = None


class APIKeyResponse(BaseModel):
    api_key: str


class APIKeyVerificationResponse(BaseModel):
    is_valid: bool
    message: str | None = None


# ── Security dashboard ────────────────────────────────────────────────────────

class APIKeySummaryAdmin(BaseModel):
    id: UUID
    name: str
    key_masked: str
    event_id: UUID | None
    event_code: str | None
    created_at: datetime
    is_cached: bool


class ActiveSession(BaseModel):
    user_id: str
    email: str | None
    expires_in_seconds: int


class SecurityOverview(BaseModel):
    total_api_keys: int
    active_sessions: int
    cached_api_keys: int
    active_carts: int


# ── Outreach dashboard ────────────────────────────────────────────────────────

class OutreachOverview(BaseModel):
    unresolved_contacts: int
    unconfirmed_partners: int
    total_contacts: int
    total_partners: int
    partners_by_type: dict[str, int]
    partners_by_tier: dict[str, int]


# ── Events dashboard ──────────────────────────────────────────────────────────

class EventDashboardItem(BaseModel):
    id: UUID
    code: str
    title: str
    start_date: date
    end_date: date
    is_active: bool
    cfp_is_open: bool
    total_proposals: int
    accepted_proposals: int
    acceptance_rate: float
    confirmed_sponsors: int
    total_speakers: int
    total_sessions: int


class EventsDashboardOverview(BaseModel):
    total_events: int
    active_events: int
    events: list[EventDashboardItem]


# ── Proposals dashboard ───────────────────────────────────────────────────────

class ProposalsDashboardOverview(BaseModel):
    total_proposals: int
    by_status: dict[str, int]
    by_session_type: dict[str, int]
    without_track: int


# ── Users dashboard ───────────────────────────────────────────────────────────

class UsersDashboardOverview(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    new_last_7_days: int
    by_role: dict[str, int]


# ── Global overview ───────────────────────────────────────────────────────────

# ── Registrations ─────────────────────────────────────────────────────────────

class RegistrationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    CHECKED_IN = "checked_in"


class RegistrationBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: str | None = None
    organization: str | None = None
    ticket_type: str = "general"


class RegistrationCreate(RegistrationBase):
    pass


class RegistrationUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    organization: str | None = None
    ticket_type: str | None = None
    notes: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RegistrationStatusUpdate(BaseModel):
    status: RegistrationStatus


class RegistrationSummary(RegistrationBase):
    id: UUID
    event_id: UUID
    user_id: UUID | None = None
    email: str
    status: RegistrationStatus
    checked_in_at: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class RegistrationsDashboard(BaseModel):
    total: int
    by_status: dict[str, int]
    by_ticket_type: dict[str, int]
    checked_in_today: int


class GlobalOverview(BaseModel):
    # users
    total_users: int
    active_users: int
    new_users_last_7_days: int
    users_by_role: dict[str, int]
    # events
    total_events: int
    active_events: int
    past_events: int
    # proposals
    total_proposals: int
    pending_proposals: int
    # participants
    total_registrations: int
    confirmed_registrations: int
    # outreach
    unresolved_contacts: int
    unconfirmed_partners: int
    # shop
    total_orders: int
    orders_by_status: dict[str, int]
    total_revenue: Decimal
    revenue_current_month: Decimal
    # security
    active_sessions: int


# event


class EventType(str, Enum):
    WORKSHOP = "workshop"
    CONFERENCE = "conference"
    DINNER = "dinner"
    COMMUNITY = "community"


class EventBase(BaseModel):
    code: str
    title: str
    tagline: str | None = None
    description: str
    location: str
    country: str = "Togo"
    city: str = "Lome"
    type: EventType = EventType.CONFERENCE
    format: DeliveryMethod = DeliveryMethod.HYBRID
    google_maps_url: HttpUrl | None = None
    timezone: str = "Africa/Lome"
    start_date: date
    end_date: date
    website_url: HttpUrl | None = None
    report_url: HttpUrl | None = None
    cfp_open_at: datetime | None = None
    cfp_close_at: datetime | None = None
    early_bird_sales_open_at: datetime | None = None
    early_bird_sales_close_at: datetime | None = None
    ticket_sales_open_at: datetime | None = None
    ticket_sales_close_at: datetime | None = None
    is_active: bool = False


class EventUpdate(BaseModel):
    title: str | None = None
    tagline: str | None = None
    description: str | None = None
    location: str | None = None
    country: str | None = None
    city: str | None = None
    type: EventType | None = None
    format: DeliveryMethod | None = None
    google_maps_url: HttpUrl | None = None
    timezone: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    website_url: HttpUrl | None = None
    report_url: HttpUrl | None = None
    cfp_open_at: datetime | None = None
    cfp_close_at: datetime | None = None
    early_bird_sales_open_at: datetime | None = None
    early_bird_sales_close_at: datetime | None = None
    ticket_sales_open_at: datetime | None = None
    ticket_sales_close_at: datetime | None = None
    is_active: bool | None = None
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class EventSummary(EventBase):
    id: UUID
    google_maps_url: str | None = None
    website_url: str | None = None
    report_url: str | None = None
    created_at: datetime
    updated_at: datetime


# track / speaker/ session
class SessionType(str, Enum):
    TALK = "talk"
    WORKSHOP = "workshop"
    PANEL = "panel"
    KEYNOTE = "keynote"
    LIGHTNING = "lightning"


class SubmissionStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WAITLISTED = "waitlisted"


class TrackBase(BaseModel):
    name: str
    description: str | None = None
    color: str | None = None


class TrackSummary(TrackBase):
    id: UUID
    event_id: UUID
    created_at: datetime
    updated_at: datetime


class TrackCreate(TrackBase):
    pass


class TrackUpdate(BaseModel):
    name: str | None = None
    event_id: UUID | None = None
    description: str | None = None
    color: str | None = None
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class ProposalBase(BaseModel):
    title: str
    description: str
    abstract: str | None = None
    level: str | None = None
    language: str = "French"
    track_id: UUID = None
    speaker_full_name: str
    speaker_email: EmailStr
    speaker_phone: str | None = None
    speaker_organization: str | None = None
    speaker_bio: str | None = None
    speaker_photo_url: str | None = None
    speaker_social_links: dict[str, HttpUrl] = Field(default_factory=dict)
    session_type: SessionType
    format: DeliveryMethod = DeliveryMethod.ONSITE
    needs_equipment: bool = False
    equipment_details: str | None = None


class ProposalCreate(ProposalBase):
    pass


class ProposalUpdate(BaseModel):
    title: str = Field(..., description="The title of the proposal")
    description: str = Field(
        ..., description="A detailed description of the proposal")
    abstract: str = Field(
        ..., description="A brief abstract summarizing the proposal")
    level: str = Field(
        ..., description="The intended audience level for the proposal (e.g., Beginner, Intermediate, Advanced)")
    language: str = Field(
        ..., description="The language in which the session will be delivered (e.g., English, French)")
    track_id: UUID = Field(
        None, description="The ID of the track to which the proposal belongs")
    speaker_full_name:  str = Field(
        ..., description="The full name of the speaker submitting the proposal")
    speaker_email: EmailStr = Field(
        ..., description="The email address of the speaker submitting the proposal")
    speaker_phone: str = Field(
        None, description="The phone number of the speaker submitting the proposal")
    speaker_organization: str = Field(
        None, description="The organization or company the speaker is affiliated with")
    speaker_bio: str = Field(
        None, description="A short biography of the speaker")
    speaker_photo_url: HttpUrl = Field(
        None, description="A URL to a photo of the speaker")
    speaker_social_links: dict[str, HttpUrl] = Field(
        None, description="A dictionary of social media links for the speaker (e.g., {'twitter': 'https://twitter.com/speaker'})")
    session_type: SessionType = Field(
        None, description="The type of the session (e.g., Talk, Workshop, Panel)")
    status: SubmissionStatus = Field(
        None, description="The current status of the proposal (e.g., Draft, Submitted, Accepted, Rejected)")
    format: DeliveryMethod = Field(
        None, description="The preferred delivery method for the session (e.g., Onsite, Online, Hybrid)")
    needs_equipment: bool = Field(
        None, description="Indicates whether the session requires any special equipment")
    equipment_details: str = Field(
        None, description="Details about the equipment needed for the session, if any")
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class ProposalSummary(ProposalBase):
    id: UUID
    event_id: UUID
    speaker_email: str = None
    speaker_photo_url: str | None = None
    speaker_social_links: dict[str, str] = Field(default_factory=dict)
    session_type: SessionType
    status: SubmissionStatus
    created_at: datetime
    updated_at: datetime


class SpeakerBase(BaseModel):
    first_name: str
    last_name: str
    full_name: str
    email: str
    headline: str | None = None
    organization: str | None = None
    country: str | None = None
    bio: str | None = None
    photo_url: HttpUrl | None = None
    social_links: dict[str, HttpUrl] = Field(default_factory=dict)
    website_url: HttpUrl | None = None


class SpeakerSummary(SpeakerBase):
    id: UUID
    event_id: UUID
    proposal_id: UUID | None = None
    photo_url: str | None = None
    social_links: dict[str, str] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class SpeakerCreate(SpeakerBase):
    proposal_id: UUID | None = None


class SpeakerUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    email: EmailStr | None = None
    headline: str | None = None
    organization: str | None = None
    country: str | None = None
    bio: str | None = None
    photo_url: HttpUrl | None = None
    social_links: dict[str, HttpUrl] | None = None
    website_url: HttpUrl | None = None
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class SessionBase(BaseModel):
    track_id: UUID | None = None
    venue_id: UUID
    proposal_id: UUID | None = None
    speaker_id: UUID | None = None
    title: str
    slug: str
    session_type: SessionType
    starts_at: datetime
    ends_at: datetime
    description: str | None = None


class SessionSummary(SessionBase):
    id: UUID
    event_id: UUID
    created_at: datetime
    updated_at: datetime


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    track_id: UUID | None = None
    venue_id: UUID | None = None
    proposal_id: UUID | None = None
    speaker_id: UUID | None = None
    title: str | None = None
    slug: str | None = None
    session_type: SessionType | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    description: str | None = None
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
