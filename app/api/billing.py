from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_business, require_business_roles
from app.core.config import settings
from app.core.database import get_db
from app.models.models import Business
from app.schemas.dashboard import BillingStatus
from app.services.usage_service import PLAN_LIMITS
from app.services.stripe_service import process_stripe_event

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Stripe webhook is not configured")
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    try:
        import stripe
        event = stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
        process_stripe_event(event, db)
        return {"received": True}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid Stripe payload") from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook") from exc


@router.get("/status", response_model=BillingStatus)
def billing_status(business: Business = Depends(get_current_business)):
    return BillingStatus(
        plan=business.plan_code or "starter_trial",
        status=business.subscription_status or "trialing",
        customer_id=business.stripe_customer_id,
        subscription_id=business.stripe_subscription_id,
        limits={**PLAN_LIMITS.get(business.plan_code or "starter_trial", {}), **(business.usage_limits or {})},
        usage_period_start=business.usage_period_start,
        usage_period_end=business.usage_period_end,
        usage={
            "messages": business.usage_messages or 0,
            "llm_tokens": business.usage_llm_tokens or 0,
            "tool_calls": business.usage_tool_calls or 0,
        },
    )


@router.post("/checkout")
def create_checkout_session(
    business: Business = Depends(get_current_business),
    _authorized_user=Depends(require_business_roles("owner", "admin")),
):
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


@router.post("/cancel")
def cancel_subscription(
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
    _authorized_user=Depends(require_business_roles("owner", "admin")),
):
    if not business.stripe_subscription_id:
        raise HTTPException(status_code=400, detail="No active subscription found")
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe billing is not configured")
    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.Subscription.modify(business.stripe_subscription_id, cancel_at_period_end=True)
        business.subscription_status = "cancelling"
        db.commit()
        return {"status": "cancelling", "cancel_at_period_end": True}
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail="Unable to cancel subscription") from exc
