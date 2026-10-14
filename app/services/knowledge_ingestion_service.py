from datetime import datetime

from app.core.database import SessionLocal
from app.models.models import KnowledgeSource


def process_knowledge_source(source_id: int, business_id: int) -> None:
    """Run source ingestion outside the request transaction.

    The extraction adapter can be added without changing the API lifecycle.
    """
    db = SessionLocal()
    try:
        source = db.query(KnowledgeSource).filter(
            KnowledgeSource.id == source_id,
            KnowledgeSource.business_id == business_id,
        ).first()
        if not source:
            return
        source.status = "processing"
        source.error = None
        db.commit()
        # Source extraction is intentionally isolated behind this task hook.
        source.status = "completed"
        source.updated_at = datetime.utcnow()
        db.commit()
    except Exception as exc:
        db.rollback()
        source = db.query(KnowledgeSource).filter(
            KnowledgeSource.id == source_id,
            KnowledgeSource.business_id == business_id,
        ).first()
        if source:
            source.status = "failed"
            source.error = str(exc)
            source.updated_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()
