from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.models import KnowledgeBaseEntry, Business
from app.api.dependencies import get_current_business
from app.api.schemas_kb import KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])

@router.post("", response_model=KnowledgeBaseResponse)
def create_entry(
    entry: KnowledgeBaseCreate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    kb_entry = KnowledgeBaseEntry(
        business_id=business.id,
        category=entry.category,
        question=entry.question,
        answer=entry.answer,
        extra_data=entry.extra_data
    )
    db.add(kb_entry)
    db.commit()
    db.refresh(kb_entry)
    return kb_entry

@router.get("", response_model=List[KnowledgeBaseResponse])
def list_entries(
    category: str = None,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    query = db.query(KnowledgeBaseEntry).filter(KnowledgeBaseEntry.business_id == business.id)
    if category:
        query = query.filter(KnowledgeBaseEntry.category == category)
    return query.all()

@router.get("/{entry_id}", response_model=KnowledgeBaseResponse)
def get_entry(
    entry_id: int,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    entry = db.query(KnowledgeBaseEntry).filter(
        KnowledgeBaseEntry.id == entry_id,
        KnowledgeBaseEntry.business_id == business.id
    ).first()
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
    entry = db.query(KnowledgeBaseEntry).filter(
        KnowledgeBaseEntry.id == entry_id,
        KnowledgeBaseEntry.business_id == business.id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    if entry_data.category is not None:
        entry.category = entry_data.category
    if entry_data.question is not None:
        entry.question = entry_data.question
    if entry_data.answer is not None:
        entry.answer = entry_data.answer
    if entry_data.extra_data is not None:
        entry.extra_data = entry_data.extra_data

    db.commit()
    db.refresh(entry)
    return entry

@router.delete("/{entry_id}")
def delete_entry(
    entry_id: int,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    entry = db.query(KnowledgeBaseEntry).filter(
        KnowledgeBaseEntry.id == entry_id,
        KnowledgeBaseEntry.business_id == business.id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    db.delete(entry)
    db.commit()
    return {"message": "Entry deleted"}
