from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class KnowledgeBaseCreate(BaseModel):
    category: str
    question: Optional[str] = None
    answer: str
    extra_data: Optional[dict] = {}

class KnowledgeBaseUpdate(BaseModel):
    category: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    extra_data: Optional[dict] = None

class KnowledgeBaseResponse(BaseModel):
    id: int
    business_id: int
    category: str
    question: Optional[str]
    answer: str
    extra_data: dict
    created_at: datetime

    class Config:
        from_attributes = True
