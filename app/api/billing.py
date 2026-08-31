from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_business
from app.core.config import settings
from app.core.database import get_db
from app.models.models import Business
from app.schemas.dashboard import BillingStatus

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


@router.get("/status", response_model=BillingStatus)
def billing_status(business: Business = Depends(get_current_business)):
    billing = (business.settings or {}).get("billing", {})
    return BillingStatus(
        plan=billing.get("plan", "starter_trial"),
        status=billing.get("status", "trialing"),
        customer_id=billing.get("customer_id"),
        subscription_id=billing.get("subscription_id"),
    )


@router.post("/checkout")
def create_checkout_session(business: Business = Depends(get_current_business)):
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_PRICE_ID:
        raise HTTPException(status_code=503, detail="Stripe billing is not configured")
    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": settings.STRIPE_PRICE_ID, "quantity": 1}],
            success_url=f"{settings.FRONTEND_URL.rstrip('/')}/dashboard/settings?billing=success",
            cancel_url=f"{settings.FRONTEND_URL.rstrip('/')}/dashboard/settings?billing=cancelled",
            client_reference_id=str(business.id),
            metadata={"business_id": str(business.id)},
        )
        return {"checkout_url": session.url}
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to create billing checkout session") from exc
