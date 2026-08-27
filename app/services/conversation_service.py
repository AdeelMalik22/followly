from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from app.models.models import Lead, Conversation, Message, LeadStatus, ConversationStatus

def get_or_create_lead(phone: str, business_id: int, db: Session) -> Lead:
    """Get existing lead or create new one"""
    lead = db.query(Lead).filter(
        Lead.phone == phone,
        Lead.business_id == business_id
    ).first()

    if not lead:
        lead = Lead(
            phone=phone,
            business_id=business_id,
            status=LeadStatus.NEW,
            source="whatsapp"
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)

    return lead

def get_or_create_conversation(lead_id: int, business_id: int, channel: str, db: Session) -> Conversation:
    """Get active conversation or create new one"""
    conversation = db.query(Conversation).filter(
        Conversation.lead_id == lead_id,
        Conversation.business_id == business_id,
        Conversation.channel == channel,
        Conversation.status == ConversationStatus.ACTIVE
    ).first()

    if not conversation:
        conversation = Conversation(
            lead_id=lead_id,
            business_id=business_id,
            channel=channel,
            status=ConversationStatus.ACTIVE
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    return conversation

def save_message(
    conversation_id: int,
    role: str,
    content: str,
    db: Session,
    whatsapp_message_id: Optional[str] = None
) -> Message:
    """Save a message to database"""
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        timestamp=datetime.utcnow(),
        whatsapp_message_id=whatsapp_message_id
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def get_conversation_history(conversation_id: int, limit: int, db: Session) -> list[Message]:
    """Get recent messages from conversation"""
    return db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.timestamp.desc()).limit(limit).all()[::-1]

def update_conversation_timestamp(conversation_id: int, db: Session):
    """Update last_message_at for conversation"""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation:
        conversation.last_message_at = datetime.utcnow()
        db.commit()

def update_lead_status(lead_id: int, status: LeadStatus, db: Session):
    """Update lead status"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if lead:
        lead.status = status
        lead.last_contact_at = datetime.utcnow()
        db.commit()
