import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.core.database import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.models.models import Business, Customer

router = APIRouter(prefix="/api/v1/customer/auth", tags=["customer-auth"])
SCOPES = ["openid", "email", "profile"]


def customer_flow() -> Flow:
    return Flow.from_client_config({"web": {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [settings.CUSTOMER_GOOGLE_REDIRECT_URI],
    }}, scopes=SCOPES, redirect_uri=settings.CUSTOMER_GOOGLE_REDIRECT_URI)


@router.get("/google")
def google_login(business_key: str, db: Session = Depends(get_db)):
    business = next((item for item in db.query(Business).all() if (item.settings or {}).get("widget_key") == business_key), None)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET or not settings.CUSTOMER_GOOGLE_REDIRECT_URI:
        raise HTTPException(status_code=503, detail="Customer Google login is not configured")
    flow = customer_flow()
    nonce = secrets.token_urlsafe(16)
    url, _ = flow.authorization_url(access_type="offline", prompt="select_account", state=f"{business.id}:{nonce}")
    return RedirectResponse(url=url)


@router.get("/callback")
def google_callback(code: str, state: str, db: Session = Depends(get_db)):
    try:
        business_id = int(state.split(":", 1)[0])
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        flow = customer_flow()
        # Google may reorder/expand identity scopes in the callback. The
        # callback is dedicated to identity login, so avoid oauthlib's
        # order-sensitive scope comparison.
        flow.oauth2session.scope = None
        flow.fetch_token(code=code)
        token_info = id_token.verify_oauth2_token(flow.credentials.id_token, google_requests.Request(), settings.GOOGLE_CLIENT_ID)
        google_id = token_info["sub"]
        customer = db.query(Customer).filter(Customer.business_id == business.id, Customer.google_id == google_id).first()
        if not customer:
            customer = Customer(business_id=business.id, google_id=google_id, email=token_info.get("email"), name=token_info.get("name"))
            db.add(customer)
        else:
            customer.email = token_info.get("email") or customer.email
            customer.name = token_info.get("name") or customer.name
        db.commit()
        access_token = create_access_token(data={"customer_id": str(customer.id), "business_id": business.id})
        chat_base = settings.API_BASE_URL.rstrip("/") or "http://localhost:8000"
        response = RedirectResponse(f"{chat_base}/chat?business_key={(business.settings or {}).get('widget_key', '')}")
        response.set_cookie("followly_customer_token", access_token, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30)
        return response
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        import logging
        logging.getLogger(__name__).exception("Customer Google OAuth callback failed")
        raise HTTPException(status_code=400, detail="Unable to sign in with Google") from exc


@router.post("/logout")
def customer_logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("followly_customer_token")
    response.delete_cookie("followly_visitor_id")
    return response
