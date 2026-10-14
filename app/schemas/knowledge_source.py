from datetime import datetime
from pydantic import BaseModel, Field


class KnowledgeSourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    source_type: str = Field(default="document", pattern="^(document|url|text)$")
    uri: str | None = None
    mime_type: str | None = None


class KnowledgeSourceResponse(BaseModel):
    id: int
    business_id: int
    name: str
    source_type: str
    uri: str | None
    mime_type: str | None
    status: str
    visibility: str
    version: int
    error: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
