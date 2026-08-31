from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import secrets

from app.api.dependencies import get_current_business, get_current_user
from app.core.database import get_db
from app.models.models import Business, User
from app.schemas.dashboard import (
    BusinessProfileResponse, BusinessProfileUpdate, BookingSettings, BookingSettingsUpdate, WidgetConfigResponse, EscalationSettings,
)

router = APIRouter(prefix="/api/v1/business", tags=["business"])


@router.get("/widget-config", response_model=WidgetConfigResponse)
def get_widget_config(business: Business = Depends(get_current_business), db: Session = Depends(get_db)):
    settings = business.settings or {}
    if not settings.get("widget_key"):
        settings["widget_key"] = secrets.token_urlsafe(24)
        business.settings = settings
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(business, "settings")
        db.commit()
    return WidgetConfigResponse(widget_key=settings.get("widget_key", ""), business_name=business.name)


@router.get("/escalation-settings", response_model=EscalationSettings)
def get_escalation_settings(business: Business = Depends(get_current_business)):
    return EscalationSettings(**((business.settings or {}).get("escalation", {})))


@router.put("/escalation-settings", response_model=EscalationSettings)
def update_escalation_settings(payload: EscalationSettings, business: Business = Depends(get_current_business), db: Session = Depends(get_db)):
    business.settings = business.settings or {}
    business.settings["escalation"] = payload.model_dump()
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(business, "settings")
    db.commit()
    return payload


@router.get("/profile", response_model=BusinessProfileResponse)
def get_profile(
    business: Business = Depends(get_current_business),
    user: User = Depends(get_current_user),
):
    return BusinessProfileResponse(
        name=business.name,
        industry=business.industry,
        owner_name=user.name,
        owner_email=user.email,
    )


@router.post("/onboarding/complete")
def complete_onboarding(business: Business = Depends(get_current_business), db: Session = Depends(get_db)):
    business.settings = business.settings or {}
    business.settings["onboarding_completed"] = True
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(business, "settings")
    db.commit()
    return {"status": "completed"}


@router.put("/profile", response_model=BusinessProfileResponse)
def update_profile(
    profile: BusinessProfileUpdate,
    business: Business = Depends(get_current_business),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business.name = profile.name.strip()
    business.industry = profile.industry.strip()
    user.name = profile.owner_name.strip()
    db.commit()
    db.refresh(business)
    db.refresh(user)
    return BusinessProfileResponse(
        name=business.name,
        industry=business.industry,
        owner_name=user.name,
        owner_email=user.email,
    )


@router.get("/booking-settings", response_model=BookingSettings)
def get_booking_settings(business: Business = Depends(get_current_business)):
    settings = business.settings or {}
    return BookingSettings(
        working_hours=settings.get("working_hours", {}),
        appointment_duration_minutes=settings.get("appointment_duration_minutes", 60),
    )


@router.put("/booking-settings", response_model=BookingSettings)
def update_booking_settings(
    payload: BookingSettingsUpdate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    if not 15 <= payload.appointment_duration_minutes <= 480:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="Appointment duration must be between 15 and 480 minutes")
    business.settings = business.settings or {}
    business.settings["working_hours"] = payload.working_hours
    business.settings["appointment_duration_minutes"] = payload.appointment_duration_minutes
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(business, "settings")
    db.commit()
    return payload
