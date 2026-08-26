from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Enum as SQLEnum
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

    users = relationship("User", back_populates="business")
    leads = relationship("Lead", back_populates="business")
    conversations = relationship("Conversation", back_populates="business")
    appointments = relationship("Appointment", back_populates="business")
    knowledge_base = relationship("KnowledgeBaseEntry", back_populates="business")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="owner")
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="users")

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
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

    conversation = relationship("Conversation", back_populates="messages")

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

class KnowledgeBaseEntry(Base):
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    category = Column(String, nullable=False)  # services, pricing, policies, faqs
    question = Column(String)
    answer = Column(Text, nullable=False)
    extra_data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="knowledge_base")

class FollowUpRule(Base):
    __tablename__ = "follow_up_rules"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    trigger_condition = Column(String, nullable=False)
    delay_hours = Column(Integer, nullable=False)
    message_template = Column(Text, nullable=False)
    active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
