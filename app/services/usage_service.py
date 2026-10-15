from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

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
    limits = plan_limits(business)
    projected = {
        "messages": (business.usage_messages or 0) + 1,
        "llm_tokens": (business.usage_llm_tokens or 0) + max(llm_tokens, 0),
        "tool_calls": (business.usage_tool_calls or 0) + max(tool_calls, 0),
    }
    for resource, value in projected.items():
        limit = limits.get(resource)
        if limit is not None and value > limit:
            raise RuntimeError(f"Tenant {resource} usage limit reached")
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


def usage_report(
    business: Business,
    db: Session,
    start: datetime | None = None,
    end: datetime | None = None,
) -> dict:
    """Aggregate usage events for a tenant and reporting period."""
    end = end or datetime.utcnow()
    start = start or business.usage_period_start or (end - timedelta(days=30))
    rows = db.query(
        UsageEvent.event_type,
        func.coalesce(func.sum(UsageEvent.llm_tokens), 0),
        func.coalesce(func.sum(UsageEvent.tool_calls), 0),
        func.count(UsageEvent.id),
    ).filter(
        UsageEvent.business_id == business.id,
        UsageEvent.created_at >= start,
        UsageEvent.created_at < end,
    ).group_by(UsageEvent.event_type).all()
    by_type = {
        event_type: {"events": int(events), "llm_tokens": int(tokens), "tool_calls": int(tools)}
        for event_type, tokens, tools, events in rows
    }
    return {
        "business_id": business.id,
        "period_start": start,
        "period_end": end,
        "totals": {
            "events": sum(item["events"] for item in by_type.values()),
            "llm_tokens": sum(item["llm_tokens"] for item in by_type.values()),
            "tool_calls": sum(item["tool_calls"] for item in by_type.values()),
        },
        "by_event_type": by_type,
    }
