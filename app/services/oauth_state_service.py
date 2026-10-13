import hashlib
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.models import OAuthState


def store_oauth_state(
    state: str,
    business_id: int,
    provider: str,
    expires_at: datetime,
    db: Session,
) -> None:
    db.add(OAuthState(
        business_id=business_id,
        state_hash=hashlib.sha256(state.encode()).hexdigest(),
        provider=provider,
        expires_at=expires_at.replace(tzinfo=None),
    ))
    db.commit()


def consume_oauth_state(state: str, business_id: int, provider: str, db: Session) -> bool:
    state_hash = hashlib.sha256(state.encode()).hexdigest()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    record = db.query(OAuthState).filter(
        OAuthState.state_hash == state_hash,
        OAuthState.business_id == business_id,
        OAuthState.provider == provider,
        OAuthState.used_at.is_(None),
        OAuthState.expires_at > now,
    ).first()
    if not record:
        return False
    record.used_at = now
    db.commit()
    return True
