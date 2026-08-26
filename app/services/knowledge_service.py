from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.models import KnowledgeBaseEntry

def create_knowledge_entry(
    business_id: int,
    category: str,
    answer: str,
    question: Optional[str] = None,
    extra_data: Optional[dict] = None,
    db: Session = None
) -> KnowledgeBaseEntry:
    """Create a new knowledge base entry"""
    kb_entry = KnowledgeBaseEntry(
        business_id=business_id,
        category=category,
        question=question,
        answer=answer,
        extra_data=extra_data or {}
    )
    db.add(kb_entry)
    db.commit()
    db.refresh(kb_entry)
    return kb_entry

def get_knowledge_entries(
    business_id: int,
    category: Optional[str] = None,
    db: Session = None
) -> List[KnowledgeBaseEntry]:
    """Get all knowledge base entries for a business"""
    query = db.query(KnowledgeBaseEntry).filter(KnowledgeBaseEntry.business_id == business_id)
    if category:
        query = query.filter(KnowledgeBaseEntry.category == category)
    return query.all()

def get_knowledge_entry_by_id(
    entry_id: int,
    business_id: int,
    db: Session = None
) -> Optional[KnowledgeBaseEntry]:
    """Get a single knowledge base entry"""
    return db.query(KnowledgeBaseEntry).filter(
        KnowledgeBaseEntry.id == entry_id,
        KnowledgeBaseEntry.business_id == business_id
    ).first()

def update_knowledge_entry(
    entry_id: int,
    business_id: int,
    category: Optional[str] = None,
    question: Optional[str] = None,
    answer: Optional[str] = None,
    extra_data: Optional[dict] = None,
    db: Session = None
) -> Optional[KnowledgeBaseEntry]:
    """Update a knowledge base entry"""
    entry = get_knowledge_entry_by_id(entry_id, business_id, db)
    if not entry:
        return None

    if category is not None:
        entry.category = category
    if question is not None:
        entry.question = question
    if answer is not None:
        entry.answer = answer
    if extra_data is not None:
        entry.extra_data = extra_data

    db.commit()
    db.refresh(entry)
    return entry

def delete_knowledge_entry(
    entry_id: int,
    business_id: int,
    db: Session = None
) -> bool:
    """Delete a knowledge base entry"""
    entry = get_knowledge_entry_by_id(entry_id, business_id, db)
    if not entry:
        return False

    db.delete(entry)
    db.commit()
    return True
