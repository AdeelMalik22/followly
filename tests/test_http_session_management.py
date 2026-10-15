from datetime import timedelta

from app.api.dependencies import get_current_user
from app.core.security import create_access_token
from app.main import app

from tests.test_http_auth_flows import http_context


def test_business_logout_revokes_user_token_over_http(http_context):
    client, db, first, second, owner, *_ = http_context
    token = create_access_token(
        {"sub": str(owner.id), "business_id": first.id, "session_version": owner.session_version},
        expires_delta=timedelta(minutes=10),
    )
    app.dependency_overrides.pop(get_current_user, None)
    client.headers["Authorization"] = f"Bearer {token}"
    assert client.get("/api/v1/auth/me").status_code == 200
    assert client.post("/api/v1/auth/logout").status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401


def test_customer_recovery_revokes_cookie_and_starts_tenant_login(http_context):
    client, db, first, *_ = http_context
    first.widget_key = "http-recovery-key"
    db.commit()
    client.cookies.set("followly_customer_token", "invalid-token")
    response = client.post(
        f"/api/v1/customer/auth/recover?business_key={first.widget_key}",
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "/api/v1/customer/auth/google" in response.headers["location"]
    assert f"business_key={first.widget_key}" in response.headers["location"]
