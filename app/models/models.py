from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

class LeadStatus(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    BOOKED = "booked"
    COLD = "cold"
    RECOVERED = "recovered"
    NOT_INTERESTED = "not_interested"

class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    COLD = "cold"
    HUMAN_TAKEOVER = "human_takeover"
    CLOSED = "closed"

class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    settings = Column(JSON, default={})
    configuration = Column(JSON, nullable=True)
    integration_health = Column(JSON, nullable=True)
    configuration_updated_at = Column(DateTime, nullable=True)
    configuration_updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    lifecycle_status = Column(String, nullable=False, default="onboarding", index=True)
    lifecycle_changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    plan_code = Column(String, nullable=False, default="starter_trial", index=True)
    subscription_status = Column(String, nullable=False, default="trialing", index=True)
    stripe_customer_id = Column(String, nullable=True, index=True)
    stripe_subscription_id = Column(String, nullable=True, index=True)
    usage_period_start = Column(DateTime, nullable=True)
    usage_period_end = Column(DateTime, nullable=True)
    usage_messages = Column(Integer, nullable=False, default=0)
    usage_llm_tokens = Column(Integer, nullable=False, default=0)
    usage_tool_calls = Column(Integer, nullable=False, default=0)
    widget_key = Column(String, unique=True, index=True, nullable=True)
    whatsapp_phone_id = Column(String, unique=True, index=True, nullable=True)
    whatsapp_access_token = Column(String, nullable=True)
    google_calendar_credentials = Column(JSON, nullable=True)
    google_calendar_credentials_encrypted = Column(Text, nullable=True)
    industry = Column(String, nullable=False, default="Dental Clinic")

    users = relationship("User", back_populates="business", foreign_keys="User.business_id")
    leads = relationship("Lead", back_populates="business")
    conversations = relationship("Conversation", back_populates="business")
    appointments = relationship("Appointment", back_populates="business")
    knowledge_base = relationship("KnowledgeBaseEntry", back_populates="business")
    customers = relationship("Customer", back_populates="business")


class OAuthState(Base):
    __tablename__ = "oauth_states"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    state_hash = Column(String, unique=True, nullable=False, index=True)
    provider = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    __table_args__ = (UniqueConstraint("business_id", "event_id", name="uq_webhook_events_business_event"),)

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    provider = Column(String, nullable=False)
    event_id = Column(String, nullable=False)
    status = Column(String, nullable=False, default="processing", index=True)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="owner")
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="users", foreign_keys=[business_id])


class TeamInvitation(Base):
    __tablename__ = "team_invitations"
    __table_args__ = (UniqueConstraint("business_id", "email", "status", name="uq_team_invites_business_email_status"),)

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    email = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False, default="staff")
    token_hash = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, nullable=False, default="pending", index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    accepted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (UniqueConstraint("business_id", "google_id", name="uq_customers_business_google_id"),)

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    email = Column(String, nullable=True, index=True)
    name = Column(String, nullable=True)
    google_id = Column(String, nullable=True, index=True)
    session_version = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="customers")
    leads = relationship("Lead", back_populates="customer")

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    phone = Column(String, index=True)
    name = Column(String)
    email = Column(String, index=True)
    status = Column(SQLEnum(LeadStatus), default=LeadStatus.NEW, index=True)
    source = Column(String)
    extra_data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    last_contact_at = Column(DateTime)

    business = relationship("Business", back_populates="leads")
    conversations = relationship("Conversation", back_populates="lead")
    appointments = relationship("Appointment", back_populates="lead")
    customer = relationship("Customer", back_populates="leads")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    channel = Column(String, nullable=False)
    status = Column(SQLEnum(ConversationStatus), default=ConversationStatus.ACTIVE, index=True)
    last_message_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="conversations")
    lead = relationship("Lead", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    extra_data = Column(JSON, default={})
    whatsapp_message_id = Column(String, unique=True, index=True, nullable=True)

    conversation = relationship("Conversation", back_populates="messages")


class ToolCallAudit(Base):
    __tablename__ = "tool_call_audits"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    tool_name = Column(String, nullable=False)
    arguments = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    success = Column(Integer, nullable=False, default=0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    conversation = relationship("Conversation")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    calendar_event_id = Column(String)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    service = Column(String)
    status = Column(String, default="scheduled")
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="appointments")
    lead = relationship("Lead", back_populates="appointments")


class AppointmentStatusHistory(Base):
    __tablename__ = "appointment_status_history"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False, index=True)
    previous_status = Column(String, nullable=False)
    new_status = Column(String, nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, index=True)

class KnowledgeBaseEntry(Base):
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    category = Column(String, nullable=False)  # services, pricing, policies, faqs
    question = Column(String)
    answer = Column(Text, nullable=False)
    extra_data = Column(JSON, default={})
    source_name = Column(String, nullable=True)
    source_uri = Column(String, nullable=True)
    source_id = Column(Integer, ForeignKey("knowledge_sources.id"), nullable=True, index=True)
    visibility = Column(String, nullable=False, default="active", index=True)
    version = Column(Integer, nullable=False, default=1)
    deleted_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="knowledge_base")
    source = relationship("KnowledgeSource", back_populates="entries")


class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    source_type = Column(String, nullable=False, default="document")
    uri = Column(String, nullable=True)
    mime_type = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending", index=True)
    visibility = Column(String, nullable=False, default="active", index=True)
    version = Column(Integer, nullable=False, default=1)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    entries = relationship("KnowledgeBaseEntry", back_populates="source")


class KnowledgeVersion(Base):
    __tablename__ = "knowledge_versions"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    entry_id = Column(Integer, ForeignKey("knowledge_base.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    question = Column(String, nullable=True)
    answer = Column(Text, nullable=False)
    extra_data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class FollowUpRule(Base):
    __tablename__ = "follow_up_rules"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    trigger_condition = Column(String, nullable=False)
    delay_hours = Column(Integer, nullable=False)
    message_template = Column(Text, nullable=False)
    active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
