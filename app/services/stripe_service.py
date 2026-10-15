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


def _plan_from_subscription(subscription) -> str | None:
    metadata = _value(subscription, "metadata", {}) or {}
    if metadata.get("plan_code") in PLAN_LIMITS:
        return metadata["plan_code"]
    items = _value(subscription, "items", {}) or {}
    data = _value(items, "data", []) or []
    if data:
        price = _value(data[0], "price", {}) or {}
        price_metadata = _value(price, "metadata", {}) or {}
        return price_metadata.get("plan_code")
    return None


def _sync_subscription_period(business: Business, subscription) -> None:
    period_start = _value(subscription, "current_period_start")
    period_end = _value(subscription, "current_period_end")
    if period_start and period_end:
        business.usage_period_start = datetime.utcfromtimestamp(period_start)
        business.usage_period_end = datetime.utcfromtimestamp(period_end)


def _apply_subscription_state(business: Business, subscription, event_type: str) -> None:
    status = _value(subscription, "status") or "active"
    if event_type.endswith("deleted"):
        status = "cancelled"
    business.stripe_customer_id = _value(subscription, "customer") or business.stripe_customer_id
    business.stripe_subscription_id = _value(subscription, "id") or business.stripe_subscription_id
    plan = _plan_from_subscription(subscription)
    if plan in PLAN_LIMITS:
        business.plan_code = plan
    business.subscription_status = status
    if status in {"active", "trialing"}:
        business.lifecycle_status = "active"
    elif status in {"canceled", "cancelled", "unpaid", "incomplete_expired"}:
        business.lifecycle_status = "suspended"
    _sync_subscription_period(business, subscription)


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
            _apply_subscription_state(business, event_object, event_type)
        elif event_type == "checkout.session.completed":
            business.stripe_customer_id = _value(event_object, "customer") or business.stripe_customer_id
            business.stripe_subscription_id = _value(event_object, "subscription") or business.stripe_subscription_id
            business.subscription_status = "active"
            business.lifecycle_status = "active"
        elif event_type == "invoice.payment_failed":
            business.subscription_status = "past_due"
        elif event_type in {"invoice.finalization_failed", "invoice.payment_action_required"}:
            business.subscription_status = "past_due"
        elif event_type == "invoice.payment_succeeded":
            if business.subscription_status not in {"cancelled", "canceled", "unpaid"}:
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
