from pydantic import BaseModel
from typing import Optional

class WhatsAppMessage(BaseModel):
    from_number: str
    message: str
    message_id: str
    timestamp: str

class WhatsAppWebhook(BaseModel):
    object: str
    entry: list

class WhatsAppSendMessage(BaseModel):
    to: str
    message: str
