from app.api.dependencies import get_current_business
from app.main import app
from app.models.models import Conversation, Message

from tests.test_http_auth_flows import http_context


def test_dashboard_test_chat_uses_tenant_configuration_and_scopes_conversations(http_context, monkeypatch):
    client, db, first, second, *_ = http_context

    async def fake_agent(conversation, business, message, db):
        assert business.id == first.id
        return f"reply:{message}"

    monkeypatch.setattr("app.api.business.process_message_with_agent", fake_agent)
    response = client.post("/api/v1/business/test-chat", json={"message": "Hello"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["response"] == "reply:Hello"
    conversation = db.query(Conversation).filter(Conversation.id == payload["conversation_id"]).one()
    assert conversation.business_id == first.id
    assert conversation.channel == "dashboard_test"
    assert db.query(Message).filter(Message.conversation_id == conversation.id).count() == 2

    app.dependency_overrides[get_current_business] = lambda: second
    assert client.post(
        "/api/v1/business/test-chat",
        json={"message": "No cross tenant", "conversation_id": conversation.id},
    ).status_code == 404
