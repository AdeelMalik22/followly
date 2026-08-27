import httpx
import hashlib
import hmac
import base64
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
    try:
        entry = webhook_data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})

        messages = value.get("messages", [])
        if not messages:
            return None

        message = messages[0]

        return {
            "from_number": message.get("from"),
            "message_id": message.get("id"),
            "timestamp": message.get("timestamp"),
            "message_type": message.get("type"),
            "text": message.get("text", {}).get("body", "") if message.get("type") == "text" else None,
            "business_phone_id": value.get("metadata", {}).get("phone_number_id")
        }
    except (KeyError, IndexError):
        return None
