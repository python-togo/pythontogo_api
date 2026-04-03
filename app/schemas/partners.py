from enum import Enum
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime, timezone


class PartnerType(str, Enum):
    """Enum for partner types."""

    PARTNERSHIP = "partnership"
    SPONSORSHIP = "sponsorship"


class SponsorPackage(Enum):
    """Enum for sponsorship packages."""

    GOLD = "Gold Package"
    SILVER = "Silver Package"
    BRONZE = "Bronze Package"
    HEART = "Heart Package"
    PLATINUM = "Platinum Package"
    HEADLINE = "Headline Package"


class Sponsorship(BaseModel):
    """Schema for sponsorship packages."""

    package: SponsorPackage = Field(..., example=SponsorPackage.GOLD)
    description: str = Field(
        None, example="Includes logo on website and social media.")
    price: float = Field(None, example=5000.00)
    currency: str = Field(None, example="USD")


class PartnerBase(BaseModel):
    """Base schema for partners."""

    name: str = Field(..., example="Tech Company")
    contact_email: str = Field(..., example="contact@techcompany.com")
    description: str = Field(None, example="A leading technology company.")
    logo_url: str = Field(None, example="https://example.com/logo.png")
    partner_type: PartnerType = Field(..., example=PartnerType.PARTNERSHIP)
    sponsorship: Sponsorship = Field(
        None, example=Sponsorship(package=SponsorPackage.GOLD))
    confirmed: bool = Field(False, example=False)
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=datetime.now(timezone.utc))


class PartnerCreate(PartnerBase):
    """Schema for creating a partner."""

    pass
