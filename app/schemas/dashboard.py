from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.models import LeadStatus, ConversationStatus


# ── Lead schemas ──────────────────────────────────────────────────────────────

class LeadResponse(BaseModel):
    id: int
    business_id: int
    phone: Optional[str]
    name: Optional[str]
    email: Optional[str]
    status: LeadStatus
    source: Optional[str]
    created_at: datetime
    last_contact_at: Optional[datetime]

    class Config:
        from_attributes = True


class LeadCreate(BaseModel):
    phone: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    source: Optional[str] = None


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    status: Optional[LeadStatus] = None


# ── Message schemas ───────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True


# ── Conversation schemas ──────────────────────────────────────────────────────

class ConversationListItem(BaseModel):
    id: int
    business_id: int
    lead_id: int
    channel: str
    status: ConversationStatus
    last_message_at: Optional[datetime]
    created_at: datetime
    lead: Optional[LeadResponse]
    last_message: Optional[MessageResponse]

    class Config:
        from_attributes = True


class ConversationDetail(BaseModel):
    id: int
    business_id: int
    lead_id: int
    channel: str
    status: ConversationStatus
    last_message_at: Optional[datetime]
    created_at: datetime
    lead: Optional[LeadResponse]

    class Config:
        from_attributes = True


class ConversationUpdate(BaseModel):
    status: ConversationStatus


class SendMessageRequest(BaseModel):
    content: str


# ── Appointment schemas ───────────────────────────────────────────────────────

class AppointmentResponse(BaseModel):
    id: int
    business_id: int
    lead_id: int
    calendar_event_id: Optional[str]
    start_time: datetime
    end_time: datetime
    service: Optional[str]
    status: str
    created_at: datetime
    lead: Optional[LeadResponse]

    class Config:
        from_attributes = True


# ── Follow-up rule schemas ────────────────────────────────────────────────────

class FollowUpRuleCreate(BaseModel):
    trigger_condition: str
    delay_hours: int
    message_template: str
    active: bool = True


class FollowUpRuleUpdate(BaseModel):
    trigger_condition: Optional[str] = None
    delay_hours: Optional[int] = None
    message_template: Optional[str] = None
    active: Optional[bool] = None


class FollowUpRuleResponse(BaseModel):
    id: int
    business_id: int
    trigger_condition: str
    delay_hours: int
    message_template: str
    active: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Analytics schemas ─────────────────────────────────────────────────────────

class FunnelSummary(BaseModel):
    total_leads: int
    contacted: int
    qualified: int
    booked: int
    recovered: int
    not_interested: int
    cold: int


class DailyLeadCount(BaseModel):
    date: str
    count: int


class AnalyticsSummary(BaseModel):
    funnel: FunnelSummary
    leads_over_time: List[DailyLeadCount]


# ── Auth / User schemas ───────────────────────────────────────────────────────

class UserMe(BaseModel):
    id: int
    email: str
    name: str
    role: str
    business_id: int
    business_name: str
    industry: str
    knowledge_base_count: int

    class Config:
        from_attributes = True
