from typing import Dict

from pydantic import BaseModel, Field


class AgentConfiguration(BaseModel):
    instructions: str = ""
    tone: str = "warm"
    language: str = "en"
    welcome_message: str = ""


class BrandingConfiguration(BaseModel):
    primary_color: str = "#2563eb"
    logo_url: str = ""


class EscalationConfiguration(BaseModel):
    contact_name: str = ""
    contact_phone: str = ""
    contact_email: str = ""
    instructions: str = ""


class ChannelConfiguration(BaseModel):
    enabled: Dict[str, bool] = Field(default_factory=dict)


class BookingConfiguration(BaseModel):
    working_hours: dict = Field(default_factory=dict)
    appointment_duration_minutes: int = Field(default=60, ge=15, le=480)


class BusinessConfiguration(BaseModel):
    agent: AgentConfiguration = Field(default_factory=AgentConfiguration)
    branding: BrandingConfiguration = Field(default_factory=BrandingConfiguration)
    escalation: EscalationConfiguration = Field(default_factory=EscalationConfiguration)
    channels: ChannelConfiguration = Field(default_factory=ChannelConfiguration)
    booking: BookingConfiguration = Field(default_factory=BookingConfiguration)

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
