from datetime import datetime, timedelta

from app.models.models import Business, KnowledgeBaseEntry, User
from app.services.usage_service import enforce_plan_limit, record_agent_usage
from tests.test_multibusiness import make_session


def test_plan_limits_cover_users_documents_storage_and_channels():
    db = make_session()
    business = Business(
        name="Limited Business",
        industry="Other",
        plan_code="starter_trial",
        usage_limits={"users": 1, "knowledge_documents": 1, "storage_bytes": 5, "channels": 1},
        configuration={"channels": {"enabled": {"web": True}}},
    )
    db.add(business)
    db.flush()
    db.add(User(business_id=business.id, email="one@example.com", name="One", hashed_password="unused"))
    db.add(KnowledgeBaseEntry(business_id=business.id, category="faq", answer="123456"))
    db.commit()
    for resource in ("users", "knowledge_documents", "storage_bytes", "channels"):
        try:
            enforce_plan_limit(business, resource, db)
        except RuntimeError as exc:
            assert "limit reached" in str(exc)
        else:
            raise AssertionError(f"{resource} limit was not enforced")


def test_agent_usage_rejects_message_llm_and_tool_overages_atomically():
    db = make_session()
    business = Business(
        name="Usage Limited Business",
        industry="Other",
        plan_code="starter_trial",
        usage_messages=1,
        usage_llm_tokens=9,
        usage_tool_calls=1,
        usage_period_start=datetime.utcnow() - timedelta(days=1),
        usage_period_end=datetime.utcnow() + timedelta(days=29),
        usage_limits={"messages": 1, "llm_tokens": 10, "tool_calls": 1},
    )
    db.add(business)
    db.commit()
    try:
        record_agent_usage(business, db, llm_tokens=1, tool_calls=0)
    except RuntimeError as exc:
        assert "messages" in str(exc)
    else:
        raise AssertionError("message limit was not enforced")
    assert business.usage_messages == 1
    assert business.usage_llm_tokens == 9

    business.usage_messages = 0
    business.usage_llm_tokens = 10
    db.commit()
    try:
        record_agent_usage(business, db, llm_tokens=1, tool_calls=0)
    except RuntimeError as exc:
        assert "llm_tokens" in str(exc)
    else:
        raise AssertionError("LLM limit was not enforced")
