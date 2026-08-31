from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import secrets

from app.api.dependencies import get_current_business, get_current_user
from app.core.database import get_db
from app.models.models import Business, User, KnowledgeBaseEntry
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
    if not business.name.strip() or not business.industry.strip():
        raise HTTPException(status_code=400, detail="Complete your business profile first")

    entries = db.query(KnowledgeBaseEntry).filter(KnowledgeBaseEntry.business_id == business.id).all()
    categories = {entry.category for entry in entries if entry.question and entry.question.strip() and entry.answer.strip()}
    required_categories = {"services", "pricing", "faqs", "policies"}
    if not required_categories.issubset(categories):
        missing = ", ".join(sorted(required_categories - categories))
        raise HTTPException(status_code=400, detail=f"Complete knowledge-base categories: {missing}")

    booking = business.settings or {}
    hours = booking.get("working_hours", {})
    valid_open_day = False
    for day in hours.values():
        if day.get("open"):
            try:
                from datetime import datetime
                start = datetime.strptime(day.get("start", ""), "%H:%M").time()
                end = datetime.strptime(day.get("end", ""), "%H:%M").time()
                valid_open_day = valid_open_day or start < end
            except (TypeError, ValueError):
                continue
    if not valid_open_day:
        raise HTTPException(status_code=400, detail="Configure at least one valid open business day")

    escalation = booking.get("escalation", {})
    if not any((escalation.get(key) or "").strip() for key in ("contact_name", "contact_phone", "contact_email", "instructions")):
        raise HTTPException(status_code=400, detail="Configure a human escalation contact or instruction")

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
