from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.models import Business
from app.api.dependencies import get_current_business
from app.api.schemas_kb import KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse
from app.services import knowledge_service

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])

@router.post("", response_model=KnowledgeBaseResponse)
def create_entry(
    entry: KnowledgeBaseCreate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return knowledge_service.create_knowledge_entry(
        business_id=business.id,
        category=entry.category,
        answer=entry.answer,
        question=entry.question,
        extra_data=entry.extra_data,
        db=db
    )

@router.get("", response_model=List[KnowledgeBaseResponse])
def list_entries(
    category: str = None,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return knowledge_service.get_knowledge_entries(business.id, category, db)

@router.get("/{entry_id}", response_model=KnowledgeBaseResponse)
def get_entry(
    entry_id: int,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    entry = knowledge_service.get_knowledge_entry_by_id(entry_id, business.id, db)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

@router.put("/{entry_id}", response_model=KnowledgeBaseResponse)
def update_entry(
    entry_id: int,
    entry_data: KnowledgeBaseUpdate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    entry = knowledge_service.update_knowledge_entry(
        entry_id=entry_id,
        business_id=business.id,
        category=entry_data.category,
        question=entry_data.question,
        answer=entry_data.answer,
        extra_data=entry_data.extra_data,
        db=db
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

@router.delete("/{entry_id}")
def delete_entry(
    entry_id: int,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    deleted = knowledge_service.delete_knowledge_entry(entry_id, business.id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"message": "Entry deleted"}
