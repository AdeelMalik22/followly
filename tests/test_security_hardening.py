from app.main import app
from app.core.security import create_access_token, decode_access_token
from app.core.config import settings
from fastapi.testclient import TestClient


def test_previous_jwt_secret_remains_valid_during_rotation(monkeypatch):
    token = create_access_token({"sub": "1"})
    current = settings.SECRET_KEY
    previous = "previous-secret-for-test"
    from jose import jwt
    rotated = jwt.encode({"sub": "1"}, previous, algorithm=settings.ALGORITHM)
    monkeypatch.setattr(settings, "JWT_PREVIOUS_SECRET_KEY", previous)
    assert decode_access_token(rotated)["sub"] == "1"
    monkeypatch.setattr(settings, "JWT_PREVIOUS_SECRET_KEY", "")
    assert decode_access_token(token)["sub"] == "1"
    assert current == settings.SECRET_KEY


def test_untrusted_origin_is_rejected_for_state_changes():
    response = TestClient(app).post("/api/v1/auth/logout", headers={"Origin": "https://evil.example"})
    assert response.status_code == 403
