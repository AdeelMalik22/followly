from datetime import datetime

from sqlalchemy.orm import Session

from app.models.models import Business
from app.schemas.business_config import BusinessConfiguration


def get_business_configuration(business: Business) -> BusinessConfiguration:
    """Load validated tenant configuration, retaining legacy settings fallback."""
    return BusinessConfiguration.model_validate(
        business.configuration or BusinessConfiguration.from_legacy_settings(business.settings).model_dump()
    )


def save_business_configuration(
    business: Business,
    configuration: BusinessConfiguration,
    db: Session,
    updated_by: int | None = None,
) -> BusinessConfiguration:
    business.configuration = configuration.model_dump()
    business.configuration_updated_at = datetime.utcnow()
    business.configuration_updated_by = updated_by
    db.commit()
    db.refresh(business)
    return configuration
