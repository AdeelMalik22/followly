import asyncio

import httpx

from app.core.config import settings
from app.core.secret_storage import decrypt_json
from app.models.models import Business
from app.services.calendar_service import get_calendar_service


async def check_whatsapp_health(business: Business) -> dict:
    if not business.whatsapp_phone_id or not business.whatsapp_access_token:
        return {"status": "disconnected", "connected": False, "error": None}
    try:
        token = business.whatsapp_access_token
        if token.startswith("fernet:"):
            from app.services.whatsapp_service import decrypt_access_token
            token = decrypt_access_token(token)
        url = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/{business.whatsapp_phone_id}"
        async with httpx.AsyncClient(timeout=settings.WHATSAPP_REQUEST_TIMEOUT) as client:
            response = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        if response.is_error:
            return {"status": "unhealthy", "connected": False, "error": f"provider_http_{response.status_code}"}
        return {"status": "healthy", "connected": True, "error": None}
    except Exception:
        return {"status": "unhealthy", "connected": False, "error": "provider_unreachable"}


async def check_calendar_health(business: Business) -> dict:
    credentials = None
    if business.google_calendar_credentials_encrypted:
        credentials = decrypt_json(business.google_calendar_credentials_encrypted)
    if not credentials and business.google_calendar_credentials:
        credentials = business.google_calendar_credentials
    if not credentials:
        return {"status": "disconnected", "connected": False, "error": None}
    try:
        service, _ = await asyncio.to_thread(get_calendar_service, credentials)
        await asyncio.to_thread(lambda: service.calendarList().list(maxResults=1).execute())
        return {"status": "healthy", "connected": True, "error": None}
    except Exception:
        return {"status": "unhealthy", "connected": False, "error": "provider_unreachable"}
