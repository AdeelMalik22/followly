import httpx
import hashlib
import hmac
import base64
import re
from typing import Optional
from app.core.config import settings
from cryptography.fernet import Fernet, InvalidToken


def _token_cipher() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
    return Fernet(key)


def encrypt_access_token(token: str) -> str:
    """Encrypt a WhatsApp access token before storing it in the database."""
    return "fernet:" + _token_cipher().encrypt(token.encode()).decode()


def decrypt_access_token(token: str) -> str:
    """Decrypt a token, supporting legacy plaintext values for migration."""
    if not token.startswith("fernet:"):
        return token
    try:
        return _token_cipher().decrypt(token[7:].encode()).decode()
    except (InvalidToken, UnicodeDecodeError) as exc:
        raise ValueError("Invalid encrypted WhatsApp access token") from exc

async def send_whatsapp_message(to: str, message: str, phone_number_id: str, access_token: str) -> dict:
    """Send a WhatsApp message via Cloud API"""
    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

def verify_webhook_token(token: str) -> bool:
    """Verify webhook verification token"""
    return token == settings.WHATSAPP_VERIFY_TOKEN


def verify_webhook_signature(payload: bytes, signature: str, app_secret: str) -> bool:
    """Verify Meta's X-Hub-Signature-256 webhook signature."""
    if not signature or not signature.startswith("sha256=") or not app_secret:
        return False

    expected_signature = hmac.new(
        app_secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()
    received_signature = signature.removeprefix("sha256=")

    return hmac.compare_digest(received_signature, expected_signature)

def parse_whatsapp_message(webhook_data: dict) -> Optional[dict]:
    """Extract message details from webhook payload"""
    if not isinstance(webhook_data, dict) or webhook_data.get("object") != "whatsapp_business_account":
        raise ValueError("Invalid WhatsApp webhook object")
    entries = webhook_data.get("entry")
    if not isinstance(entries, list) or not entries or not isinstance(entries[0], dict):
        raise ValueError("Invalid WhatsApp webhook entry")
    changes = entries[0].get("changes")
    if not isinstance(changes, list) or not changes or not isinstance(changes[0], dict):
        raise ValueError("Invalid WhatsApp webhook changes")
    value = changes[0].get("value")
    if not isinstance(value, dict):
        raise ValueError("Invalid WhatsApp webhook value")
    metadata = value.get("metadata")
    phone_id = metadata.get("phone_number_id") if isinstance(metadata, dict) else None
    if not isinstance(phone_id, str) or not phone_id.strip():
        raise ValueError("Missing WhatsApp phone ID")
    messages = value.get("messages", [])
    if not isinstance(messages, list):
        raise ValueError("Invalid WhatsApp messages")
    if not messages:
        return None
    message = messages[0]
    if not isinstance(message, dict):
        raise ValueError("Invalid WhatsApp message")
    message_id, from_number, timestamp = message.get("id"), message.get("from"), message.get("timestamp")
    if not isinstance(message_id, str) or not message_id.strip():
        raise ValueError("Missing WhatsApp message ID")
    if not isinstance(from_number, str) or not re.fullmatch(r"\d{5,15}", from_number):
        raise ValueError("Invalid WhatsApp phone number")
    if not isinstance(timestamp, str) or not timestamp.isdigit():
        raise ValueError("Invalid WhatsApp message timestamp")
    message_type = message.get("type")
    supported_types = {"text", "image", "document", "audio", "interactive", "location", "button"}
    if message_type not in supported_types:
        raise ValueError("Unsupported WhatsApp message type")

    text = None
    if message_type == "text":
        text = message.get("text", {}).get("body")
    elif message_type in {"image", "document", "audio"}:
        # Captions can be handled by the agent; media itself is acknowledged
        # until media download/vision processing is added.
        text = message.get(message_type, {}).get("caption")
    elif message_type == "button":
        text = message.get("button", {}).get("text") or message.get("button", {}).get("payload")
    elif message_type == "interactive":
        interactive = message.get("interactive", {})
        reply = interactive.get("button_reply") or interactive.get("list_reply") or {}
        text = reply.get("title") or reply.get("description") or reply.get("id")
    elif message_type == "location":
        location = message.get("location", {})
        latitude, longitude = location.get("latitude"), location.get("longitude")
        if latitude is not None and longitude is not None:
            text = f"Location shared: {latitude}, {longitude}"

    if text is not None and (not isinstance(text, str) or not text.strip()):
        raise ValueError("Invalid WhatsApp text message")
    return {
        "from_number": from_number, "message_id": message_id, "timestamp": timestamp,
        "message_type": message_type, "text": text, "business_phone_id": phone_id
    }
