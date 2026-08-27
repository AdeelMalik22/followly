from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.models.models import Lead, Conversation, Message, LeadStatus, Business
from app.api.dependencies import get_current_user, get_current_business
from app.schemas.dashboard import (
    ConversationListItem, ConversationDetail, ConversationUpdate,
    MessageResponse, SendMessageRequest, LeadResponse
)

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


@router.get("", response_model=List[ConversationListItem])
def list_conversations(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    q = db.query(Conversation).filter(Conversation.business_id == business.id)
    if status:
        q = q.filter(Conversation.status == status)
    convs = q.order_by(Conversation.last_message_at.desc()).offset(skip).limit(limit).all()

    result = []
    for conv in convs:
        lead = conv.lead
        if search:
            name_match  = lead and lead.name  and search.lower() in lead.name.lower()
            phone_match = lead and lead.phone and search in lead.phone
            if not (name_match or phone_match):
                continue
        last_msg = (
            db.query(Message)
            .filter(Message.conversation_id == conv.id)
            .order_by(Message.timestamp.desc())
            .first()
        )
        item = ConversationListItem(
            id=conv.id,
            business_id=conv.business_id,
            lead_id=conv.lead_id,
            channel=conv.channel,
            status=conv.status,
            last_message_at=conv.last_message_at,
            created_at=conv.created_at,
            lead=LeadResponse.model_validate(lead) if lead else None,
            last_message=MessageResponse.model_validate(last_msg) if last_msg else None,
        )
        result.append(item)
    return result


@router.get("/{conv_id}", response_model=ConversationDetail)
def get_conversation(
    conv_id: int,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    from fastapi import HTTPException
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.business_id == business.id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationDetail(
        id=conv.id,
        business_id=conv.business_id,
        lead_id=conv.lead_id,
        channel=conv.channel,
        status=conv.status,
        last_message_at=conv.last_message_at,
        created_at=conv.created_at,
        lead=LeadResponse.model_validate(conv.lead) if conv.lead else None,
    )


@router.get("/{conv_id}/messages", response_model=List[MessageResponse])
def get_messages(
    conv_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    from fastapi import HTTPException
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.business_id == business.id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conv_id)
        .order_by(Message.timestamp.asc())
        .offset(skip).limit(limit).all()
    )
    return [MessageResponse.model_validate(m) for m in messages]


@router.patch("/{conv_id}", response_model=ConversationDetail)
def update_conversation(
    conv_id: int,
    data: ConversationUpdate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    from fastapi import HTTPException
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.business_id == business.id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conv.status = data.status
    db.commit()
    db.refresh(conv)
    return ConversationDetail(
        id=conv.id,
        business_id=conv.business_id,
        lead_id=conv.lead_id,
        channel=conv.channel,
        status=conv.status,
        last_message_at=conv.last_message_at,
        created_at=conv.created_at,
        lead=LeadResponse.model_validate(conv.lead) if conv.lead else None,
    )


@router.post("/{conv_id}/messages", response_model=MessageResponse)
def send_human_message(
    conv_id: int,
    body: SendMessageRequest,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    """Send a human agent message during manual takeover."""
    from fastapi import HTTPException
    from datetime import datetime
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.business_id == business.id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msg = Message(
        conversation_id=conv_id,
        role="assistant",
        content=body.content,
        timestamp=datetime.utcnow(),
    )
    conv.last_message_at = msg.timestamp
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return MessageResponse.model_validate(msg)
