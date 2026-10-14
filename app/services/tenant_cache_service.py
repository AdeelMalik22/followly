import json
import logging
from typing import Any

import redis

from app.core.config import settings
from app.services.tenant_context import TenantContext

logger = logging.getLogger(__name__)
_client = None


def _redis_client():
    global _client
    if _client is None:
        _client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


def namespaced_key(context: TenantContext, key: str) -> str:
    return f"tenant:{context.business_id}:{key}"


def get_cached(context: TenantContext, key: str) -> Any | None:
    try:
        value = _redis_client().get(namespaced_key(context, key))
        return json.loads(value) if value is not None else None
    except Exception:
        logger.warning("Tenant cache read failed", exc_info=True)
        return None


def set_cached(context: TenantContext, key: str, value: Any, ttl_seconds: int = 300) -> bool:
    try:
        _redis_client().setex(namespaced_key(context, key), ttl_seconds, json.dumps(value))
        return True
    except Exception:
        logger.warning("Tenant cache write failed", exc_info=True)
        return False


def delete_cached(context: TenantContext, key: str) -> bool:
    try:
        _redis_client().delete(namespaced_key(context, key))
        return True
    except Exception:
        logger.warning("Tenant cache delete failed", exc_info=True)
        return False
