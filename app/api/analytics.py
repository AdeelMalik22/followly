from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from collections import defaultdict
from app.core.database import get_db
from app.models.models import Lead, LeadStatus, Business
from app.api.dependencies import get_current_business
from app.schemas.dashboard import AnalyticsSummary, FunnelSummary, DailyLeadCount

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(
    days: int = Query(30, ge=7, le=365),
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    leads = db.query(Lead).filter(Lead.business_id == business.id).all()

    # Funnel counts (all-time)
    counts: dict = defaultdict(int)
    for lead in leads:
        counts[lead.status.value] += 1

    funnel = FunnelSummary(
        total_leads=len(leads),
        contacted=counts[LeadStatus.CONTACTED],
        qualified=counts[LeadStatus.QUALIFIED],
        booked=counts[LeadStatus.BOOKED],
        recovered=counts[LeadStatus.RECOVERED],
        not_interested=counts[LeadStatus.NOT_INTERESTED],
        cold=counts[LeadStatus.COLD],
    )

    # Daily lead counts for the last N days
    since = datetime.utcnow() - timedelta(days=days)
    daily: dict = defaultdict(int)
    for lead in leads:
        if lead.created_at and lead.created_at >= since:
            day_key = lead.created_at.strftime("%Y-%m-%d")
            daily[day_key] += 1

    # Fill in zeros for days with no leads
    leads_over_time: List[DailyLeadCount] = []
    for i in range(days):
        day = (since + timedelta(days=i + 1)).strftime("%Y-%m-%d")
        leads_over_time.append(DailyLeadCount(date=day, count=daily.get(day, 0)))

    return AnalyticsSummary(funnel=funnel, leads_over_time=leads_over_time)
