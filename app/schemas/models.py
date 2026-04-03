from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PartnerType(str, Enum):
    PARTNERSHIP = "partnership"
    SPONSORSHIP = "sponsorship"


class PackageTier(str, Enum):
    HEADLINE = "headline"
    PLATINUM = "platinum"
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"
    HEART = "heart"
    CUSTOM = "custom"


class EventType(str, Enum):
    WORKSHOP = "workshop"
    CONFERENCE = "conference"
    DINNER = "dinner"
    COMMUNITY = "community"


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


class RegistrationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    CHECKED_IN = "checked_in"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class AdjustmentType(str, Enum):
    EXTRA_CHARGE = "extra_charge"
    DISCOUNT = "discount"
    MANUAL_CORRECTION = "manual_correction"


class AdjustmentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class HealthResponse(BaseModel):
    status: str


class MessageResponse(BaseModel):
    message: str


class PyConEditionBase(BaseModel):
    code: str
    year: int
    title: str
    location: str
    start_date: date
    end_date: date
    tagline: str | None = None
    country: str = "Togo"
    city: str = "Lome"
    timezone: str = "Africa/Lome"
    website_url: str | None = None
    report_url: str | None = None


class RoleBase(BaseModel):
    pycon_edition_id: UUID
    name: str
    description: str | None = None


class PermissionBase(BaseModel):
    code: str
    description: str | None = None


class TeamMemberBase(BaseModel):
    pycon_edition_id: UUID
    role_id: UUID | None = None
    first_name: str
    last_name: str
    full_name: str
    email: str
    password_hash: str
    phone: str | None = None
    title: str | None = None
    bio: str | None = None
    photo_url: str | None = None
    social_links: dict[str, Any] = Field(default_factory=dict)


class VenueBase(BaseModel):
    pycon_edition_id: UUID
    name: str
    address: str | None = None
    city: str | None = None
    country: str | None = None
    capacity: int | None = None


class EventBase(BaseModel):
    pycon_edition_id: UUID
    venue_id: UUID | None = None
    name: str
    slug: str
    event_type: EventType
    starts_at: datetime
    ends_at: datetime
    description: str | None = None


class TrackBase(BaseModel):
    pycon_edition_id: UUID
    name: str
    description: str | None = None
    color: str | None = None


class SpeakerBase(BaseModel):
    pycon_edition_id: UUID
    first_name: str
    last_name: str
    full_name: str
    email: str
    headline: str | None = None
    organization: str | None = None
    country: str | None = None
    bio: str | None = None
    photo_url: str | None = None
    social_links: dict[str, Any] = Field(default_factory=dict)
    website_url: str | None = None


class SessionProposalBase(BaseModel):
    pycon_edition_id: UUID
    primary_speaker_id: UUID | None = None
    title: str
    abstract: str
    level: str | None = None
    language: str = "en"
    session_type: SessionType
    duration_minutes: int = 30


class SessionBase(BaseModel):
    pycon_edition_id: UUID
    event_id: UUID | None = None
    track_id: UUID | None = None
    venue_id: UUID | None = None
    proposal_id: UUID | None = None
    title: str
    slug: str
    session_type: SessionType
    starts_at: datetime
    ends_at: datetime
    summary: str | None = None
    capacity: int | None = None


class SponsorPartnerBase(BaseModel):
    pycon_edition_id: UUID
    name: str
    website_url: str | None = None
    contact_name: str | None = None
    contact_email: str
    contact_phone: str | None = None
    description: str | None = None
    logo_url: str | None = None
    partner_type: PartnerType


class SponsorshipPackageBase(BaseModel):
    pycon_edition_id: UUID
    tier: PackageTier
    title: str
    price: Decimal
    currency: str = "USD"
    benefits: list[str] = Field(default_factory=list)
    max_slots: int | None = None


class SponsorshipBase(BaseModel):
    pycon_edition_id: UUID
    partner_id: UUID
    package_id: UUID | None = None
    amount: Decimal | None = None
    currency: str = "USD"
    signed_at: datetime | None = None
    notes: str | None = None


class TicketTypeBase(BaseModel):
    pycon_edition_id: UUID
    name: str
    description: str | None = None
    price: Decimal
    currency: str = "USD"
    quantity_total: int | None = None


class AttendeeBase(BaseModel):
    pycon_edition_id: UUID
    first_name: str
    last_name: str
    full_name: str
    email: str
    whatsapp_number: str
    discord_handle: str | None = None
    phone: str | None = None
    company: str | None = None
    job_title: str | None = None
    country: str | None = None
    city: str | None = None
    dietary_requirements: str | None = None
    accessibility_requirements: str | None = None
    consent_marketing: bool = False


class RegistrationBase(BaseModel):
    pycon_edition_id: UUID
    attendee_id: UUID
    ticket_type_id: UUID
    registration_code: str
    contact_email: str
    contact_whatsapp: str
    contact_discord_handle: str | None = None


class PaymentBase(BaseModel):
    pycon_edition_id: UUID
    registration_id: UUID
    amount: Decimal
    currency: str = "USD"
    provider: str | None = None
    provider_reference: str | None = None
    submitted_proof_url: str | None = None
    submitted_note: str | None = None
    payer_email: str | None = None
    payer_whatsapp: str | None = None
    payer_discord_handle: str | None = None


class RegistrationPaymentAdjustmentBase(BaseModel):
    pycon_edition_id: UUID
    registration_id: UUID
    adjustment_type: AdjustmentType
    amount_delta: Decimal
    reason: str


class ContactMessageCreate(BaseModel):
    pycon_edition_id: UUID | None = None
    name: str
    email: str
    subject: str | None = None
    message: str


class AttendeeRegistrationCreate(BaseModel):
    pycon_edition_id: UUID
    ticket_type_id: UUID
    first_name: str
    last_name: str
    full_name: str
    email: str
    whatsapp_number: str
    discord_handle: str | None = None
    phone: str | None = None
    company: str | None = None
    job_title: str | None = None
    country: str | None = None
    city: str | None = None
    dietary_requirements: str | None = None
    accessibility_requirements: str | None = None
    consent_marketing: bool = False


class TalkSubmissionCreate(BaseModel):
    pycon_edition_id: UUID
    primary_speaker_id: UUID | None = None
    title: str
    abstract: str
    level: str | None = None
    language: str = "en"
    session_type: SessionType = SessionType.TALK
    duration_minutes: int = 30


class WorkshopSubmissionCreate(BaseModel):
    pycon_edition_id: UUID
    primary_speaker_id: UUID | None = None
    title: str
    abstract: str
    level: str | None = None
    language: str = "en"
    duration_minutes: int = 120


class SponsorInquiryCreate(BaseModel):
    pycon_edition_id: UUID
    name: str
    contact_name: str | None = None
    contact_email: str
    contact_phone: str | None = None
    website_url: str | None = None
    description: str | None = None
    logo_url: str | None = None
    tier: PackageTier | None = None


class PartnershipInquiryCreate(BaseModel):
    pycon_edition_id: UUID
    name: str
    contact_name: str | None = None
    contact_email: str
    contact_phone: str | None = None
    website_url: str | None = None
    details: str


class SponsorSummary(BaseModel):
    name: str
    partner_type: PartnerType
    is_confirmed: bool = False


class SpeakerSummary(BaseModel):
    full_name: str
    headline: str | None = None
    organization: str | None = None


class AttendeeSummary(BaseModel):
    full_name: str
    email: str
    whatsapp_number: str
    discord_handle: str | None = None


class VenueSummary(BaseModel):
    name: str
    city: str | None = None
    country: str | None = None


class TicketSummary(BaseModel):
    name: str
    price: Decimal
    currency: str = "USD"
    is_active: bool = True


class SessionSummary(BaseModel):
    title: str
    session_type: SessionType
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class YearSponsorsResponse(BaseModel):
    edition_year: int
    items: list[SponsorSummary] = Field(default_factory=list)


class YearScheduleResponse(BaseModel):
    edition_year: int
    items: list[SessionSummary] = Field(default_factory=list)


class YearSpeakersResponse(BaseModel):
    edition_year: int
    items: list[SpeakerSummary] = Field(default_factory=list)


class YearAttendeesResponse(BaseModel):
    edition_year: int
    items: list[AttendeeSummary] = Field(default_factory=list)


class YearVenuesResponse(BaseModel):
    edition_year: int
    items: list[VenueSummary] = Field(default_factory=list)


class YearTicketsResponse(BaseModel):
    edition_year: int
    items: list[TicketSummary] = Field(default_factory=list)


class YearWorkshopsResponse(BaseModel):
    edition_year: int
    items: list[SessionSummary] = Field(default_factory=list)
