from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.auth import UserCreate, UserLogin, Token, PasswordRecoveryRequest, PasswordResetRequest
from app.schemas.dashboard import UserMe
from app.services import auth_service
from app.api.dependencies import get_current_user
from app.models.models import User, KnowledgeBaseEntry
from app.services.business_config_service import get_business_configuration
from app.core.security import decode_access_token
from app.core.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/password-recovery")
def password_recovery(payload: PasswordRecoveryRequest, db: Session = Depends(get_db)):
    """Create a short-lived reset token without revealing account existence."""
    user = auth_service.get_user_by_email(payload.email, db)
    response = {"status": "If the account exists, recovery instructions were created."}
    if user:
        token = auth_service.create_password_reset_token(user, db)
        if settings.ACCOUNT_RECOVERY_DEBUG:
            response["reset_token"] = token
    return response


@router.post("/password-reset")
def password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    if not auth_service.reset_password(payload.token, payload.password, db):
        raise HTTPException(status_code=400, detail="Invalid or expired recovery token")
    return {"status": "password_reset"}

@router.post("/signup", response_model=Token)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if user exists
        existing_user = auth_service.get_user_by_email(user_data.email, db)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create user and business
        user, business = auth_service.create_user_with_business(
            email=user_data.email,
            password=user_data.password,
            business_name=user_data.business_name,
            owner_name=user_data.owner_name,
            industry=user_data.industry,
            db=db
        )

        # Generate token
        access_token = auth_service.authenticate_user(user_data.email, user_data.password, db)
        return {"access_token": access_token}
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create account"
        )

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    try:
        access_token = auth_service.authenticate_user(user_data.email, user_data.password, db)
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        return {"access_token": access_token}
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to authenticate"
        )

@router.get("/me", response_model=UserMe)
def get_me(current_user: User = Depends(get_current_user)):
    business = current_user.business
    kb_count = len(business.knowledge_base) if business else 0
    return UserMe(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        business_id=current_user.business_id,
        business_name=business.name if business else "",
        industry=business.industry if business else "",
        knowledge_base_count=kb_count,
        onboarding_completed=get_business_configuration(business).onboarding_completed if business else False,
    )


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    token = request.headers.get("authorization", "")
    payload = decode_access_token(token[7:]) if token.lower().startswith("bearer ") else None
    if payload and str(payload.get("sub", "")).isdigit():
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        if user:
            user.session_version += 1
            db.commit()
    return {"status": "logged_out"}


@router.post("/logout-all")
def logout_all(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.session_version += 1
    db.commit()
    return {"status": "all_sessions_revoked"}
