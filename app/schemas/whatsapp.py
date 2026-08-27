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


class WhatsAppCredentialsUpdate(BaseModel):
    phone_number_id: Optional[str] = None
    access_token: Optional[str] = None


class WhatsAppTestMessage(BaseModel):
    to: str
    message: str
