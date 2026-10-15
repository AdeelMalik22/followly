from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.models import Business, StripeWebhookEvent
from app.services.usage_service import PLAN_LIMITS


def _value(data, key, default=None):
    if isinstance(data, dict):
        return data.get(key, default)
    return getattr(data, key, default)


def _business_for_event(event_object, db: Session) -> Business | None:
    metadata = _value(event_object, "metadata", {}) or {}
    business_id = metadata.get("business_id")
    subscription_id = _value(event_object, "subscription") or _value(event_object, "id")
    query = db.query(Business)
    if business_id and str(business_id).isdigit():
        business = query.filter(Business.id == int(business_id)).first()
        if business:
            return business
    return query.filter(Business.stripe_subscription_id == subscription_id).first()


def _plan_from_subscription(subscription) -> str:
    metadata = _value(subscription, "metadata", {}) or {}
    if metadata.get("plan_code") in PLAN_LIMITS:
        return metadata["plan_code"]
    items = _value(subscription, "items", {}) or {}
    data = _value(items, "data", []) or []
    if data:
        price = _value(data[0], "price", {}) or {}
        price_metadata = _value(price, "metadata", {}) or {}
        return price_metadata.get("plan_code", "starter")
    return "starter"


def _apply_stripe_event(event: dict, db: Session, record: StripeWebhookEvent) -> None:
    event_id = event["id"]
    event_type = event["type"]
    event_object = event.get("data", {}).get("object", {})
    business = _business_for_event(event_object, db)
    record.business_id = business.id if business else None
    record.status = "processed"
    record.processed_at = datetime.utcnow()
    db.add(record)

    if business:
        if event_type.startswith("customer.subscription."):
            business.stripe_customer_id = _value(event_object, "customer") or business.stripe_customer_id
            business.stripe_subscription_id = _value(event_object, "id") or business.stripe_subscription_id
            business.plan_code = _plan_from_subscription(event_object)
            status = _value(event_object, "status", "active")
            business.subscription_status = "cancelled" if event_type.endswith("deleted") else status
            business.lifecycle_status = "active" if status in {"active", "trialing"} else business.lifecycle_status
            period_start = _value(event_object, "current_period_start")
            period_end = _value(event_object, "current_period_end")
            if period_start and period_end:
                business.usage_period_start = datetime.utcfromtimestamp(period_start)
                business.usage_period_end = datetime.utcfromtimestamp(period_end)
        elif event_type == "checkout.session.completed":
            business.stripe_customer_id = _value(event_object, "customer") or business.stripe_customer_id
            business.stripe_subscription_id = _value(event_object, "subscription") or business.stripe_subscription_id
            business.subscription_status = "active"
            business.lifecycle_status = "active"
        elif event_type == "invoice.payment_failed":
            business.subscription_status = "past_due"
        elif event_type == "invoice.payment_succeeded":
            business.subscription_status = "active"
    db.commit()


def process_stripe_event(event: dict, db: Session) -> bool:
    """Apply one Stripe event exactly once; failed events remain retryable."""
    event_id = event["id"]
    event_type = event["type"]
    existing = db.query(StripeWebhookEvent).filter(StripeWebhookEvent.event_id == event_id).first()
    if existing and existing.status == "processed":
        return False
    if existing and existing.status == "processing":
        return False
    record = existing or StripeWebhookEvent(event_id=event_id, event_type=event_type)
    record.status = "processing"
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return False
    try:
        _apply_stripe_event(event, db, record)
    except Exception as exc:
        db.rollback()
        record = db.query(StripeWebhookEvent).filter(StripeWebhookEvent.event_id == event_id).first()
        if record:
            record.status = "failed"
            record.error = str(exc)[:1000]
            db.commit()
        raise
    return True
