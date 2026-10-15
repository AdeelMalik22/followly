from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_business
from app.core.database import get_db
from app.models.models import Business, KnowledgeBaseEntry, KnowledgeSource
from app.schemas.knowledge_source import KnowledgeSourceCreate, KnowledgeSourceResponse, KnowledgeSourceVisibilityUpdate
from app.schemas.knowledge_version import KnowledgeVersionResponse
from app.models.models import KnowledgeVersion
from app.services.knowledge_ingestion_service import process_knowledge_source
from app.services.usage_service import enforce_plan_limit

router = APIRouter(prefix="/api/v1/knowledge-sources", tags=["knowledge-sources"])


@router.post("", response_model=KnowledgeSourceResponse, status_code=202)
def create_source(
    payload: KnowledgeSourceCreate,
    background_tasks: BackgroundTasks,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    try:
        enforce_plan_limit(business, "knowledge_documents", db)
        enforce_plan_limit(business, "storage_bytes", db, len(payload.name) + len(payload.uri or ""))
    except RuntimeError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
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


@router.patch("/{source_id}/visibility", response_model=KnowledgeSourceResponse)
def update_source_visibility(
    source_id: int,
    payload: KnowledgeSourceVisibilityUpdate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    if payload.visibility not in {"active", "hidden"}:
        raise HTTPException(status_code=422, detail="Visibility must be active or hidden")
    source = db.query(KnowledgeSource).filter(
        KnowledgeSource.id == source_id,
        KnowledgeSource.business_id == business.id,
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Knowledge source not found")
    source.visibility = payload.visibility
    db.commit()
    db.refresh(source)
    return source


@router.get("/{source_id}/versions", response_model=list[KnowledgeVersionResponse])
def list_source_versions(
    source_id: int,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    source = db.query(KnowledgeSource.id).filter(
        KnowledgeSource.id == source_id,
        KnowledgeSource.business_id == business.id,
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Knowledge source not found")
    return db.query(KnowledgeVersion).filter(
        KnowledgeVersion.business_id == business.id,
        KnowledgeVersion.entry_id.in_(
            db.query(KnowledgeBaseEntry.id).filter(KnowledgeBaseEntry.source_id == source_id)
        ),
    ).order_by(KnowledgeVersion.created_at.desc()).all()
