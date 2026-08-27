from sqlalchemy.orm import Session
from app.models.models import User, Business
from app.core.security import get_password_hash, verify_password, create_access_token

def create_user_with_business(email: str, password: str, business_name: str, owner_name: str, industry: str, db: Session):
    """Create a new user and associated business"""
    # Create business
    business = Business(name=business_name, industry=industry)
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

    access_token = create_access_token(data={"sub": str(user.id), "business_id": user.business_id})
    return access_token

def get_user_by_email(email: str, db: Session):
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()
