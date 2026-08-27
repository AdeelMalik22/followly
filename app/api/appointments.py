from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.models.models import Lead, LeadStatus, Appointment, Business
from app.api.dependencies import get_current_business
from app.schemas.dashboard import AppointmentResponse, LeadResponse

router = APIRouter(prefix="/api/v1/appointments", tags=["appointments"])


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
        result.append(AppointmentResponse(
            id=appt.id,
            business_id=appt.business_id,
            lead_id=appt.lead_id,
            calendar_event_id=appt.calendar_event_id,
            start_time=appt.start_time,
            end_time=appt.end_time,
            service=appt.service,
            status=appt.status,
            created_at=appt.created_at,
            lead=LeadResponse.model_validate(appt.lead) if appt.lead else None,
        ))
    return result
