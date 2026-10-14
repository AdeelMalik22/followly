"""Small, idempotent maintenance operations for a scheduler or one-off job runner."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.models import Customer, TeamInvitation


def expire_team_invitations(db: Session, now: datetime | None = None) -> int:
    """Mark pending invitations past their expiry as expired."""
    now = now or datetime.utcnow()
    count = (
        db.query(TeamInvitation)
        .filter(TeamInvitation.status == "pending", TeamInvitation.expires_at <= now)
        .update({TeamInvitation.status: "expired"}, synchronize_session=False)
    )
    db.commit()
    return count


def revoke_customer_sessions(db: Session, customer_ids: list[int] | None = None) -> int:
    """Invalidate customer JWTs by advancing their per-customer session version."""
    query = db.query(Customer)
    if customer_ids:
        query = query.filter(Customer.id.in_(customer_ids))
    customers = query.all()
    for customer in customers:
        customer.session_version += 1
    db.commit()
    return len(customers)


def run_session_revocation_job(db: Session, customer_ids: list[int]) -> int:
    """Scheduler entry point for targeted session revocation requests."""
    return revoke_customer_sessions(db, customer_ids)


def run_invitation_cleanup_job(db: Session, now: datetime | None = None) -> int:
    """Scheduler entry point for invitation cleanup."""
    return expire_team_invitations(db, now)
