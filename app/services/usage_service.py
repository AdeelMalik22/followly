from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.models import Business, UsageEvent

PLAN_LIMITS = {
    "starter_trial": {"messages": 1000, "tool_calls": 2500, "llm_tokens": 250000},
    "starter": {"messages": 5000, "tool_calls": 12500, "llm_tokens": 1500000},
    "growth": {"messages": 25000, "tool_calls": 75000, "llm_tokens": 7500000},
}


def _next_period(now: datetime) -> datetime:
    return now + timedelta(days=30)


def ensure_usage_period(business: Business, db: Session, now: datetime | None = None) -> None:
    now = now or datetime.utcnow()
    if business.usage_period_end and business.usage_period_end > now:
        return
    business.usage_period_start = now
    business.usage_period_end = _next_period(now)
    business.usage_messages = 0
    business.usage_llm_tokens = 0
    business.usage_tool_calls = 0
    db.flush()


def enforce_usage_limit(business: Business, resource: str, db: Session | None = None) -> None:
    if db is not None:
        ensure_usage_period(business, db)
    limits = {**PLAN_LIMITS.get(business.plan_code or "starter_trial", {}), **(business.usage_limits or {})}
    if not limits:
        return
    current = {
        "messages": business.usage_messages,
        "tool_calls": business.usage_tool_calls,
        "llm_tokens": business.usage_llm_tokens,
    }[resource]
    if current >= limits[resource]:
        raise RuntimeError(f"Tenant {resource} usage limit reached")


def record_agent_usage(
    business: Business,
    db: Session,
    *,
    llm_tokens: int = 0,
    tool_calls: int = 0,
    metadata: dict | None = None,
) -> None:
    """Attribute one agent turn to its tenant."""
    ensure_usage_period(business, db)
    business.usage_messages = (business.usage_messages or 0) + 1
    business.usage_llm_tokens = (business.usage_llm_tokens or 0) + max(llm_tokens, 0)
    business.usage_tool_calls = (business.usage_tool_calls or 0) + max(tool_calls, 0)
    db.add(UsageEvent(
        business_id=business.id,
        event_type="agent_turn",
        llm_tokens=max(llm_tokens, 0),
        tool_calls=max(tool_calls, 0),
        event_metadata=metadata,
    ))
    db.flush()
