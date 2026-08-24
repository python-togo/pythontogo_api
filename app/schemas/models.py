from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, List
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
    INSTITUTIONAL_SUPPORT = "institutional_support"
    VENUE_SUPPORT = "venue_support"
    MEDIA_PARTNER = "media_partner"
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


class FeedbackBase(BaseModel):
    sex: str | None = None
    age: str | None = None
    profession: str | None = None
    country: str | None = None
    python_level: str | None = None
    heard: str | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    overall: str | None = None
    favorite: str | None = None
    improvements: str | None = None
    comments: str | None = None
    days: List[str] = Field(default_factory=list)


class FeedbackSummary(FeedbackBase):
    id: UUID
    is_resolved: bool = False
    created_at: datetime
    updated_at: datetime


class FeedbacksList(BaseModel):
    feedbacks: list[FeedbackSummary] = Field(
        default_factory=list)


class FeedbackUpdate(BaseModel):
    sex: str | None = None
    age: str | None = None
    profession: str | None = None
    country: str | None = None
    python_level: str | None = None
    heard: str | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    overall: str | None = None
    favorite: str | None = None
    improvements: str | None = None
    comments: str | None = None
    days: List[str] | None = None
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
    full_name: str
    email: EmailStr
    headline: str | None = None
    organization: str | None = None
    company_logo_url: str | None = None
    country: str | None = None
    bio: str
    photo_url: str
    social_links: dict[str, str] = Field(default_factory=dict)
    sessions: List[dict[str, str]] = Field(default_factory=list)
    is_featured: bool = False


class SpeakerSummary(BaseModel):
    full_name: str
    headline: str | None = None
    organization: str | None = None
    company_logo_url: str | None = None
    country: str | None = None
    bio: str
    photo_url: str
    social_links: dict[str, str] | None = Field(default_factory=dict)
    sessions: List[dict[str, str]] | None = Field(default_factory=list)
    is_featured: bool = False
    created_at: datetime
    updated_at: datetime


class SpeakerCreate(SpeakerBase):
    proposal_id: UUID | None = None


class SpeakerUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    headline: str | None = None
    organization: str | None = None
    company_logo_url: str | None = None
    country: str | None = None
    bio: str | None = None
    photo_url: str | None = None
    social_links: dict[str, str] | None = None
    sessions: List[dict[str, str]] | None = None
    is_featured: bool | None = None
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class SessionBase(BaseModel):
    event_id: UUID | None = None
    track_id: UUID | None = None
    venue_id: UUID | None = None
    speaker_id: UUID | None = None
    title: str
    slug: str
    session_type: SessionType
    starts_at: datetime
    ends_at: datetime
    description: str | None = None


class SessionSummary(SessionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    track_id: UUID | None = None
    venue_id: UUID | None = None
    speaker_id: UUID | None = None
    title: str | None = None
    slug: str | None = None
    session_type: SessionType | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    description: str | None = None
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


class RegistrationBase(BaseModel):
    full_name: str
    email: EmailStr
    whatsapp_number: str | None = None
    ticket_type: str
    ticket_id: UUID
    ticket_price: float = Field(..., ge=0,
                                description="The price of the ticket, must be possitive")
    quantity: int = Field(..., ge=1,
                          description="The quantity of tickets, must be at least 1")
    attendance_status: str = "pending"
    payment_status: str = "pending"
    dietary_restrictions: str | None = None
    payment_reference: str | None = None
    payment_link: str | None = None
    agreed_to_code_of_conduct: bool = False
    agreed_to_privacy_policy: bool = False
    shared_with_sponsors: bool = False
    success_page_url: str | None = None
    cancel_page_url: str | None = None
    file_url: str | None = None
    file_type: str | None = None
    voucher_id: UUID | None = None
    voucher_code: str | None = None


class RegistrationCreate(RegistrationBase):
    pass


class RegistrationSummary(RegistrationBase):
    id: UUID
    event_id: UUID
    created_at: datetime
    updated_at: datetime


class RegistrationUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    whatsapp_number: str | None = None
    ticket_type: str | None = None
    attendance_status: str | None = None
    payment_status: str | None = None
    dietary_restrictions: str | None = None
    payment_reference: str | None = None
    payment_link: str | None = None
    agreed_to_code_of_conduct: bool | None = None
    agreed_to_privacy_policy: bool | None = None
    shared_with_sponsors: bool | None = None
    description: str | None = None
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class TicketBase(BaseModel):
    name: str
    description: str | None = None
    price: float = Field(..., ge=0, description="Price must be non-negative")
    quantity: int = Field(..., ge=0,
                          description="Quantity must be non-negative")
    sales_start: datetime | None = None
    sales_end: datetime | None = None
    early_bird_price: float | None = Field(
        default=None, ge=0, description="Early bird price must be non-negative")


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = Field(
        default=None, ge=0, description="Price must be non-negative")
    quantity: int | None = Field(
        default=None, ge=0, description="Quantity must be non-negative")
    sales_start: datetime | None = None
    sales_end: datetime | None = None
    early_bird_price: float | None = Field(
        default=None, ge=0, description="Early bird price must be non-negative")
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class TicketSummary(TicketBase):
    id: UUID
    name: str | None = None
    description: str | None = None
    price: float | None = Field(
        default=None, ge=0, description="Price must be non-negative")
    quantity: int | None = Field(
        default=None, ge=0, description="Quantity must be non-negative")
    early_bird_price: float | None = Field(
        default=None, ge=0, description="Early bird price must be non-negative")


class TicketStudentProofPayload(BaseModel):
    fileName: str
    mimeType: str
    base64: str


class TicketBuyerPayload(BaseModel):
    fullName: str
    firstName: str
    lastName: str
    email: EmailStr
    whatsapp: str | None = None
    dietaryRestrictions: str | None = None


class TicketConsentPayload(BaseModel):
    codeOfConduct: bool
    privacyPolicy: bool
    terms: bool
    partnerSharing: bool = False


class TicketPayload(BaseModel):
    id: str
    name: str
    unitPrice: float = Field(ge=0.0)
    currency: str
    isStudent: bool = False


class TicketSubmissionPayload(BaseModel):
    ticket: TicketPayload
    quantity: int = Field(gt=0)
    total: float = Field(ge=0.0)
    buyer: TicketBuyerPayload
    consent: TicketConsentPayload
    coupon: str | None = None
    studentProof: TicketStudentProofPayload | None = None
    success_page_url: str | None = None
    cancel_page_url: str | None = None


class StudentProof(RegistrationCreate):
    file_url: str
    file_type: str


# JOB BOARD

class JobLocation(str, Enum):
    REMOTE = "remote"
    ONSITE = "onsite"
    HYBRID = "hybrid"


class ContractType(str, Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    INTERNSHIP = "internship"
    CONTRACT = "contract"


class JobOfferBase(BaseModel):
    title: str
    description: str
    company: str
    logo_url: str | None = None
    location: JobLocation
    contract_type: ContractType
    country: str | None = None
    apply_url: str
    is_active: bool = True
    salary_range: str | None = None
    application_deadline: datetime | None = None
    tags: List[str] | None = None


class JobOfferCreate(JobOfferBase):
    pass


class JobOfferUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    company: str | None = None
    logo_url: str | None = None
    location: JobLocation | None = None
    contract_type: ContractType | None = None
    country: str | None = None
    apply_url: str | None = None
    is_active: bool | None = None
    salary_range: str | None = None
    application_deadline: datetime | None = None
    tags: List[str] | None = None
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class JobOfferSummary(JobOfferBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class AttendeeID(BaseModel):
    attendee_id: UUID


class ReferralBase(BaseModel):
    referer_email: str | None = Field(
        default=None, description="Referer email must be a valid email address")
    referer_commission_percentage: float | None = Field(
        default=None, ge=0, le=100, description="Referer commission percentage must be between 0 and 100")
    referer_commission_amount: float | None = Field(
        default=None, ge=0, description="Referer commission amount must be non-negative")
    referer_full_name: str | None = Field(
        default=None, description="Referer full name must be a valid string")


class VoucherBase(BaseModel):
    prefix: str
    description: str | None = None
    discount_percentage: float | None = Field(
        default=None, ge=0, le=100, description="Discount percentage must be between 0 and 100")
    discount_amount: float | None = Field(
        default=None, ge=0, description="Discount amount must be non-negative")
    number_of_uses: int | None = Field(
        default=None, ge=0, description="Number of uses must be non-negative")
    number_of_uses_left: int | None = Field(
        default=None, ge=0, description="Number of uses left must be non-negative")
    applicable_ticket_ids: List[str] | None = None
    applicable_event_ids: List[str] | None = None
    applicable_user_emails: List[str] | None = None
    applicable_user_ids: List[str] | None = None
    referer_info: ReferralBase | None = None
    is_active: bool = True
    valid_from: datetime | None = None
    valid_until: datetime | None = None


class VoucherCreate(VoucherBase):
    pass


class VoucherUpdate(BaseModel):
    code: str | None = None
    description: str | None = None
    discount_percentage: float | None = Field(
        default=None, ge=0, le=100, description="Discount percentage must be between 0 and 100")
    discount_amount: float | None = Field(
        default=None, ge=0, description="Discount amount must be non-negative")
    number_of_uses: int | None = Field(
        default=None, ge=0, description="Number of uses must be non-negative")
    number_of_uses_left: int | None = Field(
        default=None, ge=0, description="Number of uses left must be non-negative")
    applicable_ticket_ids: List[UUID] | None = None
    applicable_event_ids: List[UUID] | None = None
    applicable_user_emails: List[str] | None = None
    applicable_user_ids: List[UUID] | None = None
    is_active: bool | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class VoucherSummary(VoucherBase):
    id: UUID
    code: str
    created_at: datetime
    updated_at: datetime


class VaucherGenerated(BaseModel):
    code: str
    message: str | None = "Voucher code generated successfully"
