from pydantic import BaseModel
from typing import Optional

class CalendarAuthRequest(BaseModel):
    business_id: int

class CalendarEventCreate(BaseModel):
    summary: str
    start_time: str
    end_time: str
    description: Optional[str] = None
    attendee_email: Optional[str] = None
