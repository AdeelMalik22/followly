from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from datetime import datetime
from app.models.models import KnowledgeBaseEntry
from app.services.tenant_context import TenantContext, knowledge_cache_key


def get_knowledge_cache_key(business_id: int, category: Optional[str] = None) -> str:
    """Return a tenant-namespaced key for knowledge retrieval caches."""
    return knowledge_cache_key(TenantContext(business_id), category)

def create_knowledge_entry(
    business_id: int,
    category: str,
    answer: str,
    question: Optional[str] = None,
    extra_data: Optional[dict] = None,
    db: Session = None,
    source_name: Optional[str] = None,
    source_uri: Optional[str] = None,
) -> KnowledgeBaseEntry:
    """Create a new knowledge base entry"""
    try:
        kb_entry = KnowledgeBaseEntry(
            business_id=business_id,
            category=category,
            question=question,
            answer=answer,
            extra_data=extra_data or {},
            source_name=source_name,
            source_uri=source_uri,
        )
        db.add(kb_entry)
        db.commit()
        db.refresh(kb_entry)
        return kb_entry
    except SQLAlchemyError:
        db.rollback()
        raise

def get_knowledge_entries(
    business_id: int,
    category: Optional[str] = None,
    db: Session = None
) -> List[KnowledgeBaseEntry]:
    """Get all knowledge base entries for a business"""
    try:
        query = db.query(KnowledgeBaseEntry).filter(
            KnowledgeBaseEntry.business_id == business_id,
            KnowledgeBaseEntry.deleted_at.is_(None),
        )
        if category:
            query = query.filter(KnowledgeBaseEntry.category == category)
        return query.all()
    except SQLAlchemyError:
        db.rollback()
        raise

def get_knowledge_entry_by_id(
    entry_id: int,
    business_id: int,
    db: Session = None
) -> Optional[KnowledgeBaseEntry]:
    """Get a single knowledge base entry"""
    try:
        return db.query(KnowledgeBaseEntry).filter(
            KnowledgeBaseEntry.id == entry_id,
            KnowledgeBaseEntry.business_id == business_id,
            KnowledgeBaseEntry.deleted_at.is_(None),
        ).first()
    except SQLAlchemyError:
        db.rollback()
        raise

def update_knowledge_entry(
    entry_id: int,
    business_id: int,
    category: Optional[str] = None,
    question: Optional[str] = None,
    answer: Optional[str] = None,
    extra_data: Optional[dict] = None,
    db: Session = None,
    source_name: Optional[str] = None,
    source_uri: Optional[str] = None,
) -> Optional[KnowledgeBaseEntry]:
    """Update a knowledge base entry"""
    try:
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
        if source_name is not None:
            entry.source_name = source_name
        if source_uri is not None:
            entry.source_uri = source_uri
        entry.version += 1

        db.commit()
        db.refresh(entry)
        return entry
    except SQLAlchemyError:
        db.rollback()
        raise

def delete_knowledge_entry(
    entry_id: int,
    business_id: int,
    db: Session = None
) -> bool:
    """Delete a knowledge base entry"""
    try:
        entry = get_knowledge_entry_by_id(entry_id, business_id, db)
        if not entry:
            return False

        entry.deleted_at = datetime.utcnow()
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        raise
