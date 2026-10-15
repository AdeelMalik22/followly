from pydantic import BaseModel, Field


class TenantDeletionRequest(BaseModel):
    confirmation: str = Field(min_length=1)
