"""Framework-neutral maintenance job entry points.

Deployments can call these from Celery, cron, or another scheduler without
coupling the application service layer to a particular worker framework.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.services.maintenance_service import (
    run_invitation_cleanup_job,
    run_session_revocation_job,
)


def cleanup_expired_invitations(db: Session, now: datetime | None = None) -> int:
    return run_invitation_cleanup_job(db, now)


def revoke_customer_sessions(db: Session, customer_ids: list[int]) -> int:
    return run_session_revocation_job(db, customer_ids)
