from sqlalchemy.orm import Session
from app.models.models import User, Business, PasswordResetToken
from app.core.security import get_password_hash, verify_password, create_access_token
from app.schemas.business_config import BusinessConfiguration
import hashlib
import secrets
from datetime import datetime, timedelta

def create_user_with_business(email: str, password: str, business_name: str, owner_name: str, industry: str, db: Session):
    """Create a new user and associated business"""
    # Create business
    widget_key = secrets.token_urlsafe(24)
    business = Business(
        name=business_name,
        industry=industry,
        widget_key=widget_key,
        settings={"widget_key": widget_key},
        configuration=BusinessConfiguration().model_dump(),
        lifecycle_status="onboarding",
        plan_code="starter_trial",
        subscription_status="trialing",
    )
    db.add(business)
    db.commit()
    db.refresh(business)

    # Create user
    hashed_password = get_password_hash(password)
    user = User(
        email=email,
        hashed_password=hashed_password,
        business_id=business.id,
        name=owner_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user, business

def authenticate_user(email: str, password: str, db: Session):
    """Authenticate user and return token"""
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None

    access_token = create_access_token(data={
        "sub": str(user.id),
        "business_id": user.business_id,
        "session_version": user.session_version,
    })
    return access_token

def get_user_by_email(email: str, db: Session):
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def create_password_reset_token(user: User, db: Session, lifetime_minutes: int = 30) -> str:
    raw_token = secrets.token_urlsafe(32)
    db.add(PasswordResetToken(
        user_id=user.id,
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
        expires_at=datetime.utcnow() + timedelta(minutes=lifetime_minutes),
    ))
    db.commit()
    return raw_token


def reset_password(raw_token: str, new_password: str, db: Session) -> bool:
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    reset = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used_at.is_(None),
        PasswordResetToken.expires_at > datetime.utcnow(),
    ).first()
    if not reset:
        return False
    user = db.query(User).filter(User.id == reset.user_id).first()
    if not user:
        return False
    user.hashed_password = get_password_hash(new_password)
    user.session_version += 1
    reset.used_at = datetime.utcnow()
    db.commit()
    return True
