from app.models.models import Business, StripeWebhookEvent
from app.services.stripe_service import process_stripe_event
from tests.test_multibusiness import make_session


def test_stripe_subscription_events_update_tenant_and_are_idempotent():
    db = make_session()
    business = Business(name="Stripe Clinic", industry="Other")
    db.add(business)
    db.commit()
    event = {
        "id": "evt_subscription_1",
        "type": "customer.subscription.updated",
        "data": {"object": {
            "id": "sub_123",
            "customer": "cus_123",
            "status": "active",
            "metadata": {"business_id": str(business.id), "plan_code": "growth"},
            "current_period_start": 1760000000,
            "current_period_end": 1762592000,
        }},
    }
    assert process_stripe_event(event, db) is True
    db.refresh(business)
    assert business.stripe_subscription_id == "sub_123"
    assert business.plan_code == "growth"
    assert business.subscription_status == "active"
    assert process_stripe_event(event, db) is False
    assert db.query(StripeWebhookEvent).filter(StripeWebhookEvent.event_id == event["id"]).count() == 1


def test_stripe_payment_failure_and_success_update_subscription_status():
    db = make_session()
    business = Business(name="Billing Business", industry="Other", stripe_subscription_id="sub_456")
    db.add(business)
    db.commit()
    failed = {"id": "evt_failed", "type": "invoice.payment_failed", "data": {"object": {"subscription": "sub_456"}}}
    succeeded = {"id": "evt_success", "type": "invoice.payment_succeeded", "data": {"object": {"subscription": "sub_456"}}}
    process_stripe_event(failed, db)
    assert business.subscription_status == "past_due"
    process_stripe_event(succeeded, db)
    assert business.subscription_status == "active"
