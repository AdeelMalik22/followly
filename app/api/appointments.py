from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Literal, Optional, List
from app.core.database import get_db
from app.models.models import Appointment, AppointmentStatusHistory, Business, Lead
from app.api.dependencies import get_current_business
from app.schemas.dashboard import AppointmentResponse, AppointmentUpdate, LeadResponse

router = APIRouter(prefix="/api/v1/appointments", tags=["appointments"])
VALID_APPOINTMENT_STATUSES = {"scheduled", "completed", "no_show", "cancelled"}
ALLOWED_STATUS_TRANSITIONS = {
    "scheduled": {"scheduled", "completed", "no_show", "cancelled"},
    "completed": {"completed"},
    "no_show": {"no_show"},
    "cancelled": {"cancelled"},
}


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
    lead_id: Optional[int] = Query(None, ge=1),
    search: Optional[str] = Query(None, min_length=1, max_length=100),
    service: Optional[str] = Query(None, min_length=1, max_length=100),
    sort: Literal["asc", "desc"] = Query("desc"),
    start_from: Optional[datetime] = Query(None, description="Appointments starting at or after this time"),
    start_to: Optional[datetime] = Query(None, description="Appointments starting before or at this time"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    if status is not None and status not in VALID_APPOINTMENT_STATUSES:
        raise HTTPException(status_code=422, detail="Invalid appointment status")
    if start_from and start_to and start_from > start_to:
        raise HTTPException(status_code=422, detail="start_from must be before start_to")

    q = db.query(Appointment).filter(Appointment.business_id == business.id)
    if status:
        q = q.filter(Appointment.status == status)
    if lead_id:
        q = q.filter(Appointment.lead_id == lead_id)
    if search:
        search_pattern = f"%{search}%"
        q = q.join(Lead).filter(
            (Lead.name.ilike(search_pattern))
            | (Lead.phone.ilike(search_pattern))
            | (Lead.email.ilike(search_pattern))
        )
    if service:
        q = q.filter(Appointment.service.ilike(f"%{service}%"))
    if start_from:
        q = q.filter(Appointment.start_time >= start_from)
    if start_to:
        q = q.filter(Appointment.start_time <= start_to)
    ordering = Appointment.start_time.asc() if sort == "asc" else Appointment.start_time.desc()
    appointments = q.order_by(ordering).offset(skip).limit(limit).all()
    result = []
    for appt in appointments:
        result.append(_appointment_response(appt))
    return result


@router.get("/summary")
def appointment_summary(
    start_from: Optional[datetime] = Query(None, description="Appointments starting at or after this time"),
    start_to: Optional[datetime] = Query(None, description="Appointments starting before or at this time"),
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    if start_from and start_to and start_from > start_to:
        raise HTTPException(status_code=422, detail="start_from must be before start_to")

    query = db.query(Appointment.status, func.count(Appointment.id)).filter(
        Appointment.business_id == business.id,
    )
    if start_from:
        query = query.filter(Appointment.start_time >= start_from)
    if start_to:
        query = query.filter(Appointment.start_time <= start_to)
    rows = query.group_by(Appointment.status).all()
    counts = {status: 0 for status in VALID_APPOINTMENT_STATUSES}
    counts.update({status: count for status, count in rows})
    return counts


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
    if payload.status not in ALLOWED_STATUS_TRANSITIONS.get(appointment.status, set()):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot change appointment status from {appointment.status} to {payload.status}",
        )

    previous_status = appointment.status
    appointment.status = payload.status
    db.add(AppointmentStatusHistory(
        business_id=business.id,
        appointment_id=appointment.id,
        previous_status=previous_status,
        new_status=payload.status,
    ))
    db.commit()
    db.refresh(appointment)
    return _appointment_response(appointment)
