from app.models.models import Business, KnowledgeBaseEntry, User
from app.services.usage_service import enforce_plan_limit
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
