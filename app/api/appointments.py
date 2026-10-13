from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.models.models import Appointment, Business
from app.api.dependencies import get_current_business
from app.schemas.dashboard import AppointmentResponse, AppointmentUpdate, LeadResponse

router = APIRouter(prefix="/api/v1/appointments", tags=["appointments"])
VALID_APPOINTMENT_STATUSES = {"scheduled", "completed", "no_show", "cancelled"}


def _appointment_response(appointment: Appointment) -> AppointmentResponse:
    return AppointmentResponse(
        id=appointment.id,
        business_id=appointment.business_id,
        lead_id=appointment.lead_id,
        calendar_event_id=appointment.calendar_event_id,
        start_time=appointment.start_time,
        end_time=appointment.end_time,
        service=appointment.service,
        status=appointment.status,
        created_at=appointment.created_at,
        lead=LeadResponse.model_validate(appointment.lead) if appointment.lead else None,
    )


@router.get("", response_model=List[AppointmentResponse])
def list_appointments(
    status: Optional[str] = Query(None, description="scheduled|completed|no_show|cancelled"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    q = db.query(Appointment).filter(Appointment.business_id == business.id)
    if status:
        q = q.filter(Appointment.status == status)
    appointments = q.order_by(Appointment.start_time.desc()).offset(skip).limit(limit).all()
    result = []
    for appt in appointments:
        result.append(_appointment_response(appt))
    return result


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: int,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.business_id == business.id,
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return _appointment_response(appointment)


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: int,
    payload: AppointmentUpdate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    if payload.status not in VALID_APPOINTMENT_STATUSES:
        raise HTTPException(status_code=422, detail="Invalid appointment status")

    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.business_id == business.id,
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.status = payload.status
    db.commit()
    db.refresh(appointment)
    return _appointment_response(appointment)
