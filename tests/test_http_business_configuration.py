from app.api.dependencies import get_current_user
from app.main import app

from tests.test_http_auth_flows import http_context


def test_business_configuration_api_round_trips_agent_branding_and_channels(http_context):
    client, *_ = http_context
    response = client.put(
        "/api/v1/business/configuration",
        json={
            "agent": {
                "instructions": "Be concise",
                "tone": "professional",
                "language": "en",
                "welcome_message": "Welcome",
            },
            "branding": {"primary_color": "#ABCDEF", "logo_url": "https://example.com/logo.png"},
            "escalation": {"contact_name": "Owner"},
            "channels": {"enabled": {"web": True, "whatsapp": False}},
            "booking": {
                "working_hours": {"monday": {"open": True, "start": "09:00", "end": "17:00"}},
                "appointment_duration_minutes": 30,
            },
        },
    )
    assert response.status_code == 200
    assert response.json()["branding"]["primary_color"] == "#abcdef"
    assert client.get("/api/v1/business/configuration").json()["agent"]["tone"] == "professional"


def test_business_configuration_api_rejects_invalid_values(http_context):
    client, *_ = http_context
    invalid = client.put(
        "/api/v1/business/configuration",
        json={"branding": {"primary_color": "blue"}},
    )
    assert invalid.status_code == 422

    invalid_hours = client.put(
        "/api/v1/business/configuration",
        json={"booking": {"working_hours": {"monday": {"open": True, "start": "17:00", "end": "09:00"}}}},
    )
    assert invalid_hours.status_code == 422


def test_business_configuration_api_requires_admin_or_owner_for_writes(http_context):
    client, *_ = http_context
    app.dependency_overrides[get_current_user] = lambda: http_context[6]
    response = client.put("/api/v1/business/configuration", json={})
    assert response.status_code == 403
