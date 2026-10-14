from app.api.dependencies import get_current_business
from app.main import app
from tests.test_http_auth_flows import http_context


def test_knowledge_crud_and_tenant_scope_are_enforced_over_http(http_context):
    client, db, first, second, *_ = http_context
    created = client.post(
        "/api/v1/knowledge",
        json={"category": "faq", "question": "Hours?", "answer": "9-5"},
    )
    assert created.status_code == 200
    entry_id = created.json()["id"]
    assert client.get(f"/api/v1/knowledge/{entry_id}").status_code == 200

    updated = client.put(
        f"/api/v1/knowledge/{entry_id}",
        json={"answer": "8-6"},
    )
    assert updated.status_code == 200
    assert updated.json()["answer"] == "8-6"

    app.dependency_overrides[get_current_business] = lambda: second
    assert client.get(f"/api/v1/knowledge/{entry_id}").status_code == 404
    assert client.put(f"/api/v1/knowledge/{entry_id}", json={"answer": "leak"}).status_code == 404
    assert client.delete(f"/api/v1/knowledge/{entry_id}").status_code == 404

    app.dependency_overrides[get_current_business] = lambda: first
    assert client.delete(f"/api/v1/knowledge/{entry_id}").status_code == 200
    assert client.get(f"/api/v1/knowledge/{entry_id}").status_code == 404


def test_lead_and_follow_up_rule_http_writes_are_tenant_scoped(http_context):
    client, db, first, second, *_ = http_context
    lead = client.post("/api/v1/leads", json={"name": "Lead", "phone": "555"})
    assert lead.status_code == 201
    lead_id = lead.json()["id"]
    assert client.patch(f"/api/v1/leads/{lead_id}", json={"name": "Updated"}).status_code == 200

    rule = client.post(
        "/api/v1/follow-up-rules",
        json={
            "trigger_condition": "new_lead",
            "delay_hours": 2,
            "message_template": "Hello",
        },
    )
    assert rule.status_code == 201
    rule_id = rule.json()["id"]
    assert client.put(
        f"/api/v1/follow-up-rules/{rule_id}",
        json={"delay_hours": 4},
    ).status_code == 200

    app.dependency_overrides[get_current_business] = lambda: second
    assert client.patch(f"/api/v1/leads/{lead_id}", json={"name": "leak"}).status_code == 404
    assert client.put(f"/api/v1/follow-up-rules/{rule_id}", json={"delay_hours": 8}).status_code == 404
    assert client.delete(f"/api/v1/follow-up-rules/{rule_id}").status_code == 404

    app.dependency_overrides[get_current_business] = lambda: first
    assert client.delete(f"/api/v1/follow-up-rules/{rule_id}").status_code == 204
