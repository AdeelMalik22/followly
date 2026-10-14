from app.models.models import Business, ConfigurationAudit, User
from app.schemas.business_config import BusinessConfiguration
from app.services.business_config_service import save_business_configuration
from tests.test_multibusiness import make_session


def test_configuration_saves_create_immutable_audit_snapshots():
    db = make_session()
    business = Business(name="Audit Clinic", industry="Dental Clinic")
    user = User(business_id=1, email="audit@example.com", name="Owner", hashed_password="unused")
    db.add(business)
    db.flush()
    user.business_id = business.id
    db.add(user)
    db.commit()

    first = BusinessConfiguration()
    first.agent.tone = "warm"
    save_business_configuration(business, first, db, updated_by=user.id)
    second = BusinessConfiguration()
    second.agent.tone = "professional"
    save_business_configuration(business, second, db, updated_by=user.id)

    audits = db.query(ConfigurationAudit).filter(ConfigurationAudit.business_id == business.id).order_by(ConfigurationAudit.id).all()
    assert len(audits) == 2
    assert audits[0].configuration["agent"]["tone"] == "warm"
    assert audits[1].configuration["agent"]["tone"] == "professional"
