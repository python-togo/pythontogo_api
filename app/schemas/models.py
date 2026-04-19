from datetime import date, datetime, timezone
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
    is_confirmed: bool | None = None
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


class APIKeyResponse(BaseModel):
    api_key: str


class APIKeyVerificationResponse(BaseModel):
    is_valid: bool
    message: str | None = None


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


class SessionSummary(SessionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    track_id: UUID | None = None
    venue_id: UUID | None = None
    proposal_id: UUID | None = None
    title: str | None = None
    slug: str | None = None
    session_type: SessionType | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    summary: str | None = None
    capacity: int | None = None
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


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
