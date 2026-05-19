from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any
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
    website_url: str | None = None
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


class AuthenticatedUser(UserSummary):
    """UserSummary enriched with RBAC claims extracted from the JWT."""
    is_admin: bool = False
    permissions: list[str] = Field(default_factory=list)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: str | None = None
    email: str | None = None


class APIKeyCreate(BaseModel):
    name: str
    event_id: UUID | None = None


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
    name_fr: str
    name_en: str
    description_fr: str | None = None
    description_en: str | None = None
    color: str | None = None


class TrackSummary(TrackBase):
    id: UUID
    event_id: UUID
    created_at: datetime
    updated_at: datetime


class TrackCreate(TrackBase):
    pass


class TrackUpdate(BaseModel):
    name_fr: str | None = None
    name_en: str | None = None
    event_id: UUID | None = None
    description_fr: str | None = None
    description_en: str | None = None
    color: str | None = None
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class TalkTopicBase(BaseModel):
    name_fr: str
    name_en: str
    description_fr: str | None = None
    description_en: str | None = None


class TopicCreate(TalkTopicBase):
    pass


class TopicSummary(TopicCreate):
    id: UUID
    event_id: UUID
    created_at: datetime
    updated_at: datetime


class TopicUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class ProposalBase(BaseModel):
    title: str
    description: str
    abstract: str | None = None
    topic_id: UUID | None = None
    format: str
    python_percentage: int | None = Field(default=None, ge=0, le=100)
    full_name: str
    email: EmailStr
    phone_number: str | None = None
    organization: str | None = None
    bio: str
    country: str
    experience: str
    photo_url: str | None = None
    social_media_links: dict[Any, Any] = Field(default_factory=dict)
    language: str = "French"
    level: str
    needs_equipment: bool = False
    equipment_details: str | None = None
    delivery_mode: DeliveryMethod = DeliveryMethod.ONSITE.value
    status: SubmissionStatus = SubmissionStatus.DRAFT.value
    agreed_to_code_of_conduct: bool = False
    agreed_to_privacy_policy: bool = False
    shared_with_sponsors: bool = False


class ProposalCreate(ProposalBase):
    pass


class ProposalUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    abstract: str | None = None
    topic_id: UUID | None = None
    format: str | None = None
    python_percentage: int | None = Field(default=None, ge=0, le=100)
    full_name: str | None = None
    email: EmailStr | None = None
    phone_number: str | None = None
    organization: str | None = None
    bio: str | None = None
    country: str | None = None
    experience: str | None = None
    photo_url: str | None = None
    social_media_links: dict[Any, Any] | None = None
    language: str | None = None
    level: str | None = None
    needs_equipment: bool | None = None
    equipment_details: str | None = None
    delivery_mode: DeliveryMethod | None = None
    status: SubmissionStatus | None = None
    agreed_to_code_of_conduct: bool | None = None
    agreed_to_privacy_policy: bool | None = None
    shared_with_sponsors: bool | None = None
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class ProposalDraftData(BaseModel):
    title: str | None = None
    description: str | None = None
    abstract: str | None = None
    topic_id: UUID | None = None
    format: str | None = None
    python_percentage: int | None = Field(default=None, ge=0, le=100)
    full_name: str | None = None
    email: EmailStr | None = None
    phone_number: str | None = None
    organization: str | None = None
    bio: str | None = None
    country: str | None = None
    experience: str | None = None
    photo_url: str | None = None
    social_media_links: dict[Any, Any] | None = None
    language: str | None = None
    level: str | None = None
    needs_equipment: bool | None = None
    equipment_details: str | None = None
    delivery_mode: DeliveryMethod | None = None
    status: SubmissionStatus | None = None
    agreed_to_code_of_conduct: bool | None = None
    agreed_to_privacy_policy: bool | None = None
    shared_with_sponsors: bool | None = None


class ProposalDraft(BaseModel):
    email: str
    password_hash: str
    proposal_data: ProposalDraftData


class ResumeDraft(BaseModel):
    email: EmailStr
    password: str


class ResumeDraftResponse(BaseModel):
    proposal_data: ProposalDraftData


class ProposalSummary(ProposalBase):
    id: UUID
    event_id: UUID
    email: str
    photo_url: str | None = None
    social_media_links: dict[Any, Any] = Field(default_factory=dict)
    status: SubmissionStatus = SubmissionStatus.DRAFT
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
    social_links: dict[str, str] = Field(default_factory=dict)
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


<<<<<<< HEAD
# ── RBAC ──────────────────────────────────────────────────────────────────────

class PermissionSummary(BaseModel):
    id: UUID
    name: str
    description: str | None
    resource: str
    action: str
    created_at: datetime


class RoleSummary(BaseModel):
    id: UUID
    name: str
    description: str | None
    is_system: bool
    created_at: datetime
    updated_at: datetime


class RoleDetail(RoleSummary):
    permissions: list[PermissionSummary] = Field(default_factory=list)


class RoleCreate(BaseModel):
    name: str
    description: str | None = None


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class AssignPermissionsRequest(BaseModel):
    permission_ids: list[UUID]


class AssignRoleRequest(BaseModel):
    role_id: UUID


class UserRoleAssignment(BaseModel):
    user_id: UUID
    role_id: UUID
    role_name: str
    assigned_at: datetime


# ── CFP Review ────────────────────────────────────────────────────────────────

class TalkReviewCreate(BaseModel):
    score: int = Field(..., ge=1, le=5, description="Rating from 1 (poor) to 5 (excellent)")
    comment: str | None = None


class TalkReviewSummary(BaseModel):
    id: UUID
    proposal_id: UUID
    reviewer_id: UUID
    score: int
    comment: str | None
    created_at: datetime
    updated_at: datetime


class TalkReviewMasked(BaseModel):
    """Returned to reviewers who have not yet voted — hides individual scores."""
    proposal_id: UUID
    has_reviewed: bool
    total_reviews: int


class TalkStatusUpdate(BaseModel):
    status: SubmissionStatus


class ProposalWithScore(ProposalSummary):
    avg_score: float | None = None
    review_count: int = 0
=======
class ProposalFormatBase(BaseModel):
    name_fr: str
    name_en: str
    description_fr: str | None = None
    description_en: str | None = None


class ProposalFormatCreate(ProposalFormatBase):
    pass


class ProposalFormatUpdate(BaseModel):
    name_fr: str | None = None
    name_en: str | None = None
    description_fr: str | None = None
    description_en: str | None = None
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class ProposalFormatSummary(ProposalFormatBase):
    id: UUID
    event_id: UUID
    created_at: datetime
    updated_at: datetime
>>>>>>> origin/main
