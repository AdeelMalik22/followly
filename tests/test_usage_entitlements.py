from datetime import datetime, timedelta

from app.models.models import Business
from app.services.usage_service import ensure_usage_period, enforce_usage_limit
from tests.test_multibusiness import make_session


def test_usage_period_rollover_resets_counters_and_assigns_next_period():
    db = make_session()
    business = Business(
        name="Usage Clinic",
        industry="Dental Clinic",
        usage_period_start=datetime(2025, 12, 1),
        usage_period_end=datetime(2025, 12, 31),
        usage_messages=10,
        usage_llm_tokens=20,
        usage_tool_calls=30,
    )
    db.add(business)
    db.commit()
    now = datetime(2026, 1, 1)
    ensure_usage_period(business, db, now)
    assert business.usage_messages == 0
    assert business.usage_llm_tokens == 0
    assert business.usage_tool_calls == 0
    assert business.usage_period_start == now
    assert business.usage_period_end == now + timedelta(days=30)


def test_custom_usage_limits_override_plan_entitlements():
    db = make_session()
    business = Business(name="Limited Clinic", industry="Dental Clinic", usage_limits={"messages": 1})
    db.add(business)
    db.commit()
    business.usage_messages = 1
    try:
        enforce_usage_limit(business, "messages")
    except RuntimeError as error:
        assert "messages usage limit" in str(error)
    else:
        raise AssertionError("custom message limit was not enforced")
