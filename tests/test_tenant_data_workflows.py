from app.models.models import Business, Lead, User
from app.services.tenant_data_service import delete_tenant_data, export_tenant_data
from tests.test_multibusiness import make_session


def test_tenant_export_is_scoped_and_deletion_removes_business_data():
    db = make_session()
    first = Business(name="Exported", industry="Other")
    second = Business(name="Kept", industry="Other")
    db.add_all([first, second])
    db.flush()
    db.add_all([
        User(business_id=first.id, email="first@example.com", name="First", hashed_password="secret"),
        Lead(business_id=first.id, phone="111", name="Lead"),
        Lead(business_id=second.id, phone="222", name="Other"),
    ])
    db.commit()
    exported = export_tenant_data(first.id, db)
    assert len(exported["leads"]) == 1
    assert exported["users"][0]["email"] == "first@example.com"
    assert "hashed_password" not in exported["users"][0]
    assert delete_tenant_data(first.id, db) is True
    assert db.query(Business).filter(Business.id == first.id).first() is None
    assert db.query(Business).filter(Business.id == second.id).first() is not None
