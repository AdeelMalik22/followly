from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class KnowledgeBaseCreate(BaseModel):
    category: str
    question: Optional[str] = None
    answer: str
    extra_data: Optional[dict] = {}
    source_name: Optional[str] = None
    source_uri: Optional[str] = None

class KnowledgeBaseUpdate(BaseModel):
    category: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    extra_data: Optional[dict] = None
    source_name: Optional[str] = None
    source_uri: Optional[str] = None

class KnowledgeBaseResponse(BaseModel):
    id: int
    business_id: int
    category: str
    question: Optional[str]
    answer: str
    extra_data: dict
    created_at: datetime
    source_name: Optional[str]
    source_uri: Optional[str]
    version: int
    deleted_at: Optional[datetime]

    class Config:
        from_attributes = True
