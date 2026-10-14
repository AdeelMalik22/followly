from datetime import datetime, timedelta

from app.models.models import Customer, TeamInvitation
from app.services.maintenance_service import expire_team_invitations, revoke_customer_sessions
from tests.test_multibusiness import make_session


def test_invitation_cleanup_marks_only_expired_pending_records():
    db = make_session()
    expired = TeamInvitation(
        business_id=1,
        email="expired@example.com",
        role="staff",
        token_hash="expired-token",
        status="pending",
        expires_at=datetime.utcnow() - timedelta(minutes=1),
    )
    active = TeamInvitation(
        business_id=1,
        email="active@example.com",
        role="staff",
        token_hash="active-token",
        status="pending",
        expires_at=datetime.utcnow() + timedelta(minutes=1),
    )
    db.add_all([expired, active])
    db.commit()

    assert expire_team_invitations(db) == 1
    assert expired.status == "expired"
    assert active.status == "pending"


def test_session_revocation_job_advances_only_requested_customers():
    db = make_session()
    first = Customer(business_id=1, google_id="customer-one", session_version=0)
    second = Customer(business_id=1, google_id="customer-two", session_version=3)
    db.add_all([first, second])
    db.commit()

    assert revoke_customer_sessions(db, [first.id]) == 1
    db.refresh(first)
    db.refresh(second)
    assert first.session_version == 1
    assert second.session_version == 3
