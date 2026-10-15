from app.core.config import settings
from app.main import app

from tests.test_http_auth_flows import http_context


def test_subscription_cancel_requires_an_active_subscription(http_context):
    client, *_ = http_context
    response = client.post("/api/v1/billing/cancel")
    assert response.status_code == 400


def test_subscription_cancel_updates_local_state_after_stripe_accepts(http_context, monkeypatch):
    client, db, first, *_ = http_context
    first.stripe_subscription_id = "sub_test"
    db.commit()
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "test-secret")

    class FakeSubscription:
        @staticmethod
        def modify(subscription_id, cancel_at_period_end):
            assert subscription_id == "sub_test"
            assert cancel_at_period_end is True
            return {"id": subscription_id}

    class FakeStripe:
        api_key = None
        Subscription = FakeSubscription

    monkeypatch.setitem(__import__("sys").modules, "stripe", FakeStripe)
    response = client.post("/api/v1/billing/cancel")
    assert response.status_code == 200
    db.refresh(first)
    assert first.subscription_status == "cancelling"
