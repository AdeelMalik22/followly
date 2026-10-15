from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.models import Business, UsageEvent, User, KnowledgeBaseEntry, KnowledgeSource

PLAN_LIMITS = {
    "starter_trial": {"messages": 1000, "tool_calls": 2500, "llm_tokens": 250000, "users": 5, "knowledge_documents": 25, "storage_bytes": 5_000_000, "channels": 1},
    "starter": {"messages": 5000, "tool_calls": 12500, "llm_tokens": 1500000, "users": 5, "knowledge_documents": 250, "storage_bytes": 50_000_000, "channels": 3},
    "growth": {"messages": 25000, "tool_calls": 75000, "llm_tokens": 7500000, "users": 20, "knowledge_documents": 2000, "storage_bytes": 500_000_000, "channels": 5},
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


def plan_limits(business: Business) -> dict:
    return {**PLAN_LIMITS.get(business.plan_code or "starter_trial", {}), **(business.usage_limits or {})}


def enforce_plan_limit(business: Business, resource: str, db: Session, additional: int = 1) -> None:
    limit = plan_limits(business).get(resource)
    if limit is None:
        return
    if resource == "users":
        current = db.query(User).filter(User.business_id == business.id).count()
    elif resource == "knowledge_documents":
        current = db.query(KnowledgeBaseEntry).filter(
            KnowledgeBaseEntry.business_id == business.id,
            KnowledgeBaseEntry.deleted_at.is_(None),
        ).count()
        current += db.query(KnowledgeSource).filter(KnowledgeSource.business_id == business.id).count()
    elif resource == "storage_bytes":
        entries = db.query(KnowledgeBaseEntry).filter(KnowledgeBaseEntry.business_id == business.id).all()
        sources = db.query(KnowledgeSource).filter(KnowledgeSource.business_id == business.id).all()
        current = sum(len((entry.question or "") + entry.answer) for entry in entries)
        current += sum(len(source.name or "") + len(source.uri or "") for source in sources)
    elif resource == "channels":
        current = sum(1 for enabled in (getattr(business, "configuration", None) or {}).get("channels", {}).get("enabled", {}).values() if enabled)
    else:
        return
    if current + additional > limit:
        raise RuntimeError(f"Tenant {resource} limit reached")


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
