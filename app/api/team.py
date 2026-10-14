import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_business, get_current_user, require_business_roles
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.models import Business, TeamInvitation, User
from app.schemas.team import TeamInvitationAccept, TeamInvitationCreate, TeamInvitationResponse, TeamRoleUpdate

router = APIRouter(prefix="/api/v1/team", tags=["team"])


def _hash_invitation_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@router.post("/invitations", response_model=TeamInvitationResponse, status_code=201)
def create_invitation(
    payload: TeamInvitationCreate,
    business: Business = Depends(get_current_business),
    _authorized_user=Depends(require_business_roles("owner", "admin")),
    db: Session = Depends(get_db),
):
    email = str(payload.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="User already exists")
    existing = db.query(TeamInvitation).filter(
        TeamInvitation.business_id == business.id,
        TeamInvitation.email == email,
        TeamInvitation.status == "pending",
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Invitation already pending")
    raw_token = secrets.token_urlsafe(32)
    invitation = TeamInvitation(
        business_id=business.id,
        email=email,
        role=payload.role,
        token_hash=_hash_invitation_token(raw_token),
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    result = TeamInvitationResponse.model_validate(invitation)
    return {**result.model_dump(), "invitation_token": raw_token}


@router.post("/invitations/accept")
def accept_invitation(payload: TeamInvitationAccept, db: Session = Depends(get_db)):
    invitation = db.query(TeamInvitation).filter(
        TeamInvitation.token_hash == _hash_invitation_token(payload.token),
        TeamInvitation.status == "pending",
    ).first()
    if not invitation or invitation.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invitation is invalid or expired")
    if db.query(User).filter(User.email == invitation.email).first():
        raise HTTPException(status_code=409, detail="User already exists")
    user = User(
        business_id=invitation.business_id,
        email=invitation.email,
        name=payload.name.strip(),
        hashed_password=get_password_hash(payload.password),
        role=invitation.role,
    )
    invitation.status = "accepted"
    invitation.accepted_at = datetime.utcnow()
    db.add(user)
    db.commit()
    return {"status": "accepted", "user_id": user.id, "business_id": user.business_id}


@router.patch("/members/{user_id}/role")
def update_member_role(
    user_id: int,
    payload: TeamRoleUpdate,
    business: Business = Depends(get_current_business),
    _authorized_user=Depends(require_business_roles("owner", "admin")),
    db: Session = Depends(get_db),
):
    member = db.query(User).filter(User.id == user_id, User.business_id == business.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    if member.role == "owner":
        raise HTTPException(status_code=400, detail="Transfer ownership before changing the owner role")
    member.role = payload.role
    db.commit()
    return {"id": member.id, "email": member.email, "role": member.role}
