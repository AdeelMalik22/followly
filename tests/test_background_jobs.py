from app.models.models import BackgroundJob
from app.services.background_job_service import enqueue_job, run_job
from tests.test_multibusiness import make_session


def test_background_job_retries_then_dead_letters():
    db = make_session()
    job = enqueue_job(db, "test", {"business_id": 10}, business_id=10, max_attempts=2)
    assert run_job(db, job.id, lambda payload: (_ for _ in ()).throw(RuntimeError("failed"))) == "pending"
    db.refresh(job)
    job.available_at = job.created_at
    db.commit()
    assert run_job(db, job.id, lambda payload: (_ for _ in ()).throw(RuntimeError("failed again"))) == "dead_letter"
    db.refresh(job)
    assert job.status == "dead_letter"
    assert job.business_id == 10
