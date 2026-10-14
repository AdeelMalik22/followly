from datetime import datetime
from pydantic import BaseModel


class KnowledgeVersionResponse(BaseModel):
    id: int
    entry_id: int
    version: int
    category: str
    question: str | None
    answer: str
    extra_data: dict
    created_at: datetime

    class Config:
        from_attributes = True
