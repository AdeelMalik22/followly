from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_business, get_current_user
from app.core.database import get_db
from app.models.models import Business, User
from app.schemas.dashboard import BusinessProfileResponse, BusinessProfileUpdate

router = APIRouter(prefix="/api/v1/business", tags=["business"])


@router.get("/profile", response_model=BusinessProfileResponse)
def get_profile(
    business: Business = Depends(get_current_business),
    user: User = Depends(get_current_user),
):
    return BusinessProfileResponse(
        name=business.name,
        industry=business.industry,
        owner_name=user.name,
        owner_email=user.email,
    )


@router.put("/profile", response_model=BusinessProfileResponse)
def update_profile(
    profile: BusinessProfileUpdate,
    business: Business = Depends(get_current_business),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business.name = profile.name.strip()
    business.industry = profile.industry.strip()
    user.name = profile.owner_name.strip()
    db.commit()
    db.refresh(business)
    db.refresh(user)
    return BusinessProfileResponse(
        name=business.name,
        industry=business.industry,
        owner_name=user.name,
        owner_email=user.email,
    )
