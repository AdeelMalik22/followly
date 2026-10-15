from datetime import datetime, timedelta

from app.models.models import Business, UsageEvent
from app.services.usage_service import usage_report
from tests.test_multibusiness import make_session


def test_usage_report_aggregates_only_the_tenant_and_requested_period():
    db = make_session()
    first = Business(name="First", industry="Other")
    second = Business(name="Second", industry="Other")
    db.add_all([first, second])
    db.flush()
    start = datetime(2026, 1, 1)
    db.add_all([
        UsageEvent(business_id=first.id, event_type="agent_turn", llm_tokens=100, tool_calls=2, created_at=start + timedelta(hours=1)),
        UsageEvent(business_id=first.id, event_type="agent_turn", llm_tokens=50, tool_calls=1, created_at=start + timedelta(hours=2)),
        UsageEvent(business_id=second.id, event_type="agent_turn", llm_tokens=999, tool_calls=9, created_at=start + timedelta(hours=1)),
    ])
    db.commit()
    report = usage_report(first, db, start, start + timedelta(days=1))
    assert report["business_id"] == first.id
    assert report["totals"] == {"events": 2, "llm_tokens": 150, "tool_calls": 3}
    assert report["by_event_type"]["agent_turn"]["events"] == 2
