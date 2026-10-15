from pydantic import BaseModel, Field


class TestChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: int | None = None


class TestChatResponse(BaseModel):
    conversation_id: int
    response: str
