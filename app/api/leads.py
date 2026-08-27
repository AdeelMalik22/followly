from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from app.core.database import get_db
from app.models.models import Lead, LeadStatus, Business
from app.api.dependencies import get_current_business
from app.schemas.dashboard import LeadResponse, LeadCreate, LeadUpdate

router = APIRouter(prefix="/api/v1/leads", tags=["leads"])


@router.get("", response_model=List[LeadResponse])
def list_leads(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    q = db.query(Lead).filter(Lead.business_id == business.id)
    if status:
        q = q.filter(Lead.status == status)
    if search:
        q = q.filter(
            (Lead.name.ilike(f"%{search}%")) |
            (Lead.phone.ilike(f"%{search}%")) |
            (Lead.email.ilike(f"%{search}%"))
        )
    leads = q.order_by(Lead.created_at.desc()).offset(skip).limit(limit).all()
    return [LeadResponse.model_validate(l) for l in leads]


@router.post("", response_model=LeadResponse, status_code=201)
def create_lead(
    data: LeadCreate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    lead = Lead(
        business_id=business.id,
        phone=data.phone,
        name=data.name,
        email=data.email,
        source=data.source or "manual",
        status=LeadStatus.NEW,
        created_at=datetime.utcnow(),
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return LeadResponse.model_validate(lead)


@router.patch("/{lead_id}", response_model=LeadResponse)
def update_lead(
    lead_id: int,
    data: LeadUpdate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.business_id == business.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if data.name is not None:
        lead.name = data.name
    if data.email is not None:
        lead.email = data.email
    if data.status is not None:
        lead.status = data.status
    db.commit()
    db.refresh(lead)
    return LeadResponse.model_validate(lead)
