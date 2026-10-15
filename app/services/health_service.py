from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import engine


def check_database() -> dict:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as exc:
        return {"status": "unhealthy", "error": type(exc).__name__}


def check_redis() -> dict:
    try:
        import redis
        redis.from_url(settings.REDIS_URL, socket_connect_timeout=1, socket_timeout=1).ping()
        return {"status": "healthy"}
    except Exception as exc:
        return {"status": "unhealthy", "error": type(exc).__name__}


def check_llm() -> dict:
    configured = any((settings.OPENROUTER_API_KEY, settings.OPENAI_API_KEY, settings.ANTHROPIC_API_KEY))
    return {"status": "configured" if configured else "unconfigured", "provider": settings.LLM_PROVIDER}


def check_queue() -> dict:
    result = check_redis()
    return {"status": result["status"], "backend": "redis/celery", **({"error": result["error"]} if "error" in result else {})}


def readiness_report() -> dict:
    checks = {
        "database": check_database(),
        "redis": check_redis(),
        "llm": check_llm(),
        "queue": check_queue(),
    }
    ready = all(check["status"] in {"healthy", "configured"} for check in checks.values())
    return {"status": "ready" if ready else "degraded", "checks": checks}
