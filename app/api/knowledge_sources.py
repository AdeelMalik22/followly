from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_business
from app.core.database import get_db
from app.models.models import Business, KnowledgeSource
from app.schemas.knowledge_source import KnowledgeSourceCreate, KnowledgeSourceResponse
from app.services.knowledge_ingestion_service import process_knowledge_source

router = APIRouter(prefix="/api/v1/knowledge-sources", tags=["knowledge-sources"])


@router.post("", response_model=KnowledgeSourceResponse, status_code=202)
def create_source(
    payload: KnowledgeSourceCreate,
    background_tasks: BackgroundTasks,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    source = KnowledgeSource(
        business_id=business.id,
        name=payload.name.strip(),
        source_type=payload.source_type,
        uri=payload.uri,
        mime_type=payload.mime_type,
        status="pending",
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    background_tasks.add_task(process_knowledge_source, source.id, business.id)
    return source


@router.get("", response_model=list[KnowledgeSourceResponse])
def list_sources(
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    return db.query(KnowledgeSource).filter(KnowledgeSource.business_id == business.id).order_by(KnowledgeSource.created_at.desc()).all()


@router.get("/{source_id}", response_model=KnowledgeSourceResponse)
def get_source(
    source_id: int,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    source = db.query(KnowledgeSource).filter(
        KnowledgeSource.id == source_id,
        KnowledgeSource.business_id == business.id,
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Knowledge source not found")
    return source
