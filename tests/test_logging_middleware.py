from fastapi.testclient import TestClient

from app.main import app


def test_correlation_id_is_returned_and_generated_for_requests():
    client = TestClient(app)
    supplied = client.get("/", headers={"X-Correlation-ID": "request-123"})
    assert supplied.headers["x-correlation-id"] == "request-123"
    generated = client.get("/")
    assert generated.headers["x-correlation-id"]
