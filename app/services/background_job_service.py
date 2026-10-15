from datetime import datetime, timedelta
from typing import Callable

from sqlalchemy.orm import Session

from app.models.models import BackgroundJob


def enqueue_job(db: Session, job_type: str, payload: dict, business_id: int | None = None, max_attempts: int = 3) -> BackgroundJob:
    job = BackgroundJob(
        business_id=business_id,
        job_type=job_type,
        payload=payload,
        max_attempts=max(1, max_attempts),
        available_at=datetime.utcnow(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def run_job(db: Session, job_id: int, handler: Callable[[dict], None]) -> str:
    job = db.query(BackgroundJob).filter(BackgroundJob.id == job_id).first()
    if not job or job.status in {"completed", "dead_letter"}:
        return "ignored"
    if job.available_at > datetime.utcnow():
        return "deferred"
    job.status = "processing"
    job.attempts += 1
    db.commit()
    try:
        handler(job.payload)
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.last_error = None
        db.commit()
        return "completed"
    except Exception as exc:
        job.last_error = str(exc)[:1000]
        if job.attempts >= job.max_attempts:
            job.status = "dead_letter"
        else:
            job.status = "pending"
            job.available_at = datetime.utcnow() + timedelta(minutes=2 ** job.attempts)
        db.commit()
        return job.status
