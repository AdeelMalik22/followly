from typing import Dict

from pydantic import BaseModel, Field, field_validator
import re


class AgentConfiguration(BaseModel):
    instructions: str = ""
    tone: str = "warm"
    language: str = "en"
    welcome_message: str = ""


class BrandingConfiguration(BaseModel):
    primary_color: str = "#2563eb"
    logo_url: str = ""

    @field_validator("primary_color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise ValueError("primary_color must be a six-digit hex color")
        return value.lower()

    @field_validator("logo_url")
    @classmethod
    def validate_logo_url(cls, value: str) -> str:
        if value and not value.startswith(("https://", "http://")):
            raise ValueError("logo_url must use http:// or https://")
        return value


class EscalationConfiguration(BaseModel):
    contact_name: str = ""
    contact_phone: str = ""
    contact_email: str = ""
    instructions: str = ""


class ChannelConfiguration(BaseModel):
    enabled: Dict[str, bool] = Field(default_factory=dict)

    @field_validator("enabled")
    @classmethod
    def validate_channels(cls, value: Dict[str, bool]) -> Dict[str, bool]:
        allowed = {"web", "whatsapp", "google_calendar"}
        unknown = set(value) - allowed
        if unknown:
            raise ValueError(f"Unsupported channels: {', '.join(sorted(unknown))}")
        return value


class BookingConfiguration(BaseModel):
    working_hours: dict = Field(default_factory=dict)
    appointment_duration_minutes: int = Field(default=60, ge=15, le=480)

    @field_validator("working_hours")
    @classmethod
    def validate_working_hours(cls, value: dict) -> dict:
        allowed_days = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
        for day, hours in value.items():
            if day not in allowed_days or not isinstance(hours, dict):
                raise ValueError("working_hours must use weekday names and objects")
            if hours.get("open"):
                for key in ("start", "end"):
                    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", str(hours.get(key, ""))):
                        raise ValueError("open working hours require HH:MM start and end")
                if hours["start"] >= hours["end"]:
                    raise ValueError("working-hours start must precede end")
        return value


class BusinessDetailsConfiguration(BaseModel):
    company_size: str = ""
    inventory_management: bool | None = None


class BusinessConfiguration(BaseModel):
    business_details: BusinessDetailsConfiguration = Field(default_factory=BusinessDetailsConfiguration)
    agent: AgentConfiguration = Field(default_factory=AgentConfiguration)
    branding: BrandingConfiguration = Field(default_factory=BrandingConfiguration)
    escalation: EscalationConfiguration = Field(default_factory=EscalationConfiguration)
    channels: ChannelConfiguration = Field(default_factory=ChannelConfiguration)
    booking: BookingConfiguration = Field(default_factory=BookingConfiguration)
    onboarding_completed: bool = False

    @classmethod
    def from_legacy_settings(cls, settings: dict | None) -> "BusinessConfiguration":
        settings = settings or {}
        return cls(
            agent=AgentConfiguration(**(settings.get("agent") or {})),
            branding=BrandingConfiguration(**(settings.get("branding") or {})),
            escalation=EscalationConfiguration(**(settings.get("escalation") or {})),
            channels=ChannelConfiguration(**(settings.get("channels") or {})),
            booking=BookingConfiguration(
                working_hours=settings.get("working_hours", {}),
                appointment_duration_minutes=settings.get("appointment_duration_minutes", 60),
            ),
        )
