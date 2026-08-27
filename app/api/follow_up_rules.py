from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.core.database import get_db
from app.models.models import FollowUpRule, Business
from app.api.dependencies import get_current_business
from app.schemas.dashboard import FollowUpRuleCreate, FollowUpRuleUpdate, FollowUpRuleResponse

router = APIRouter(prefix="/api/v1/follow-up-rules", tags=["follow-up-rules"])


@router.get("", response_model=List[FollowUpRuleResponse])
def list_rules(
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    rules = db.query(FollowUpRule).filter(
        FollowUpRule.business_id == business.id
    ).order_by(FollowUpRule.delay_hours.asc()).all()
    return [FollowUpRuleResponse.model_validate(r) for r in rules]


@router.post("", response_model=FollowUpRuleResponse, status_code=201)
def create_rule(
    data: FollowUpRuleCreate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    rule = FollowUpRule(
        business_id=business.id,
        trigger_condition=data.trigger_condition,
        delay_hours=data.delay_hours,
        message_template=data.message_template,
        active=1 if data.active else 0,
        created_at=datetime.utcnow(),
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return FollowUpRuleResponse.model_validate(rule)


@router.put("/{rule_id}", response_model=FollowUpRuleResponse)
def update_rule(
    rule_id: int,
    data: FollowUpRuleUpdate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    rule = db.query(FollowUpRule).filter(
        FollowUpRule.id == rule_id, FollowUpRule.business_id == business.id
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    if data.trigger_condition is not None:
        rule.trigger_condition = data.trigger_condition
    if data.delay_hours is not None:
        rule.delay_hours = data.delay_hours
    if data.message_template is not None:
        rule.message_template = data.message_template
    if data.active is not None:
        rule.active = 1 if data.active else 0
    db.commit()
    db.refresh(rule)
    return FollowUpRuleResponse.model_validate(rule)


@router.delete("/{rule_id}", status_code=204)
def delete_rule(
    rule_id: int,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    rule = db.query(FollowUpRule).filter(
        FollowUpRule.id == rule_id, FollowUpRule.business_id == business.id
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
