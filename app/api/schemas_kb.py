from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class KnowledgeBaseCreate(BaseModel):
    category: str
    question: Optional[str] = None
    answer: str
    metadata: Optional[dict] = {}

class KnowledgeBaseUpdate(BaseModel):
    category: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    metadata: Optional[dict] = None

class KnowledgeBaseResponse(BaseModel):
    id: int
    business_id: int
    category: str
    question: Optional[str]
    answer: str
    metadata: dict
    created_at: datetime

    class Config:
        from_attributes = True
