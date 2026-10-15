from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.models import (
    Appointment, AppointmentStatusHistory, BackgroundJob, Business, ConfigurationAudit,
    Conversation, Customer, FollowUpRule, KnowledgeBaseEntry, KnowledgeSource,
    KnowledgeVersion, Lead, Message, OAuthState, StripeWebhookEvent, TeamInvitation,
    ToolCallAudit, UsageEvent, User, WebhookEvent,
)


def _row(item: Any, fields: tuple[str, ...]) -> dict:
    values = {}
    for field in fields:
        value = getattr(item, field)
        if isinstance(value, datetime):
            value = value.isoformat()
        elif hasattr(value, "value"):
            value = value.value
        values[field] = value
    return values


def export_tenant_data(business_id: int, db: Session) -> dict:
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        return {}
    result = {
        "exported_at": datetime.utcnow().isoformat(),
        "business": _row(business, ("id", "name", "industry", "configuration", "plan_code", "subscription_status")),
    }
    collections = {
        "users": (User, ("id", "email", "name", "role", "created_at")),
        "customers": (Customer, ("id", "email", "name", "google_id", "created_at")),
        "leads": (Lead, ("id", "customer_id", "phone", "name", "email", "status", "source", "created_at")),
        "conversations": (Conversation, ("id", "lead_id", "channel", "status", "created_at")),
        "appointments": (Appointment, ("id", "lead_id", "start_time", "end_time", "service", "status", "created_at")),
        "knowledge": (KnowledgeBaseEntry, ("id", "category", "question", "answer", "source_name", "source_uri", "version", "created_at")),
        "knowledge_sources": (KnowledgeSource, ("id", "name", "source_type", "uri", "mime_type", "status", "version", "created_at")),
        "follow_up_rules": (FollowUpRule, ("id", "trigger_condition", "delay_hours", "message_template", "active", "created_at")),
        "usage_events": (UsageEvent, ("id", "event_type", "llm_tokens", "tool_calls", "event_metadata", "created_at")),
        "configuration_audits": (ConfigurationAudit, ("id", "changed_by", "configuration", "created_at")),
    }
    for name, (model, fields) in collections.items():
        result[name] = [_row(item, fields) for item in db.query(model).filter(model.business_id == business_id).all()]
    return result


def delete_tenant_data(business_id: int, db: Session) -> bool:
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        return False
    conversation_ids = [row[0] for row in db.query(Conversation.id).filter(Conversation.business_id == business_id).all()]
    lead_ids = [row[0] for row in db.query(Lead.id).filter(Lead.business_id == business_id).all()]
    if conversation_ids:
        db.query(ToolCallAudit).filter(ToolCallAudit.conversation_id.in_(conversation_ids)).delete(synchronize_session=False)
        db.query(Message).filter(Message.conversation_id.in_(conversation_ids)).delete(synchronize_session=False)
    if lead_ids:
        db.query(Appointment).filter(Appointment.lead_id.in_(lead_ids)).delete(synchronize_session=False)
    db.query(AppointmentStatusHistory).filter(AppointmentStatusHistory.business_id == business_id).delete(synchronize_session=False)
    db.query(KnowledgeVersion).filter(KnowledgeVersion.business_id == business_id).delete(synchronize_session=False)
    for model in (Conversation, Appointment, Lead, KnowledgeBaseEntry, KnowledgeSource, FollowUpRule, UsageEvent,
                  ConfigurationAudit, TeamInvitation, Customer, User, OAuthState, WebhookEvent,
                  StripeWebhookEvent, BackgroundJob):
        db.query(model).filter(model.business_id == business_id).delete(synchronize_session=False)
    db.delete(business)
    db.commit()
    return True
