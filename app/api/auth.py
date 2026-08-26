from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.schemas import UserCreate, UserLogin, Token
from app.services import auth_service

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/signup", response_model=Token)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = auth_service.get_user_by_email(user_data.email, db)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user and business
    user, business = auth_service.create_user_with_business(
        email=user_data.email,
        password=user_data.password,
        business_name=user_data.business_name,
        db=db
    )

    # Generate token
    access_token = auth_service.authenticate_user(user_data.email, user_data.password, db)
    return {"access_token": access_token}

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    access_token = auth_service.authenticate_user(user_data.email, user_data.password, db)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    return {"access_token": access_token}
