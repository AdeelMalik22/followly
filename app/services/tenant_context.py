from dataclasses import dataclass

from app.models.models import Business, Conversation


@dataclass(frozen=True)
class TenantContext:
    business_id: int

    @classmethod
    def from_business(cls, business: Business) -> "TenantContext":
        return cls(business_id=business.id)

    def validate_conversation(self, conversation: Conversation) -> None:
        if conversation.business_id != self.business_id:
            raise ValueError("Conversation does not belong to tenant context")


def knowledge_cache_key(context: TenantContext, category: str | None = None) -> str:
    suffix = category or "all"
    return f"tenant:{context.business_id}:knowledge:{suffix}"


def prompt_cache_key(context: TenantContext, configuration_version: str = "current") -> str:
    return f"tenant:{context.business_id}:prompt:{configuration_version}"
