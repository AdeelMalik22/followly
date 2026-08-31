from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_business, get_current_user
from app.core.database import get_db
from app.models.models import Business, User
from app.schemas.dashboard import (
    BusinessProfileResponse, BusinessProfileUpdate, BookingSettings, BookingSettingsUpdate,
)

router = APIRouter(prefix="/api/v1/business", tags=["business"])


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
