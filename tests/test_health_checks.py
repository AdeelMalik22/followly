def test_readiness_report_aggregates_dependency_checks(monkeypatch):
    from app.services import health_service

    monkeypatch.setattr(health_service, "check_database", lambda: {"status": "healthy"})
    monkeypatch.setattr(health_service, "check_redis", lambda: {"status": "healthy"})
    monkeypatch.setattr(health_service, "check_queue", lambda: {"status": "healthy"})
    monkeypatch.setattr(health_service, "check_llm", lambda: {"status": "configured"})
    report = health_service.readiness_report()
    assert report["status"] == "ready"
    assert set(report["checks"]) == {"database", "redis", "llm", "queue"}
