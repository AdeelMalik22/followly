from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.models import WebhookEvent


def claim_webhook_event(
    business_id: int,
    provider: str,
    event_id: str,
    db: Session,
) -> bool:
    """Atomically claim a tenant-scoped webhook event for processing."""
    existing = db.query(WebhookEvent).filter(
        WebhookEvent.business_id == business_id,
        WebhookEvent.provider == provider,
        WebhookEvent.event_id == event_id,
    ).first()
    if existing:
        if existing.status != "failed":
            return False
        existing.status = "processing"
        existing.error = None
        existing.processed_at = None
        db.commit()
        return True
    event = WebhookEvent(
        business_id=business_id,
        provider=provider,
        event_id=event_id,
        status="processing",
    )
    db.add(event)
    try:
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False


def complete_webhook_event(
    business_id: int,
    provider: str,
    event_id: str,
    db: Session,
    error: str | None = None,
) -> None:
    event = db.query(WebhookEvent).filter(
        WebhookEvent.business_id == business_id,
        WebhookEvent.provider == provider,
        WebhookEvent.event_id == event_id,
    ).first()
    if event:
        event.status = "failed" if error else "processed"
        event.error = error
        event.processed_at = datetime.utcnow()
        db.commit()


def recover_stale_webhook_events(db: Session, timeout_minutes: int = 15) -> int:
    """Mark abandoned processing claims failed so provider retries can recover them."""
    cutoff = datetime.utcnow() - timedelta(minutes=timeout_minutes)
    events = db.query(WebhookEvent).filter(
        WebhookEvent.status == "processing",
        WebhookEvent.received_at < cutoff,
    ).all()
    for event in events:
        event.status = "failed"
        event.error = "Processing timeout; eligible for retry"
        event.processed_at = datetime.utcnow()
    db.commit()
    return len(events)
