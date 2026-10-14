from sqlalchemy.orm import Session

from app.models.models import Business, UsageEvent


def record_agent_usage(
    business: Business,
    db: Session,
    *,
    llm_tokens: int = 0,
    tool_calls: int = 0,
    metadata: dict | None = None,
) -> None:
    """Attribute one agent turn to its tenant."""
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
