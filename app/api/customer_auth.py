import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.core.database import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.models.models import Business, Customer
from app.services.oauth_state_service import consume_oauth_state, store_oauth_state

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


def _create_oauth_state(business_id: int, nonce: str) -> str:
    payload = {
        "business_id": business_id,
        "nonce": nonce,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _decode_oauth_state(state: str) -> dict:
    try:
        return jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=400, detail="Invalid OAuth state") from exc


@router.get("/google")
def google_login(business_key: str, db: Session = Depends(get_db)):
    business = db.query(Business).filter(
        Business.widget_key == business_key
    ).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET or not settings.CUSTOMER_GOOGLE_REDIRECT_URI:
        raise HTTPException(status_code=503, detail="Customer Google login is not configured")
    flow = customer_flow()
    nonce = secrets.token_urlsafe(16)
    state = _create_oauth_state(business.id, nonce)
    store_oauth_state(
        state,
        business.id,
        "google_customer",
        datetime.now(timezone.utc) + timedelta(minutes=10),
        db,
    )
    url, _ = flow.authorization_url(access_type="offline", prompt="select_account", state=state, nonce=nonce)
    return RedirectResponse(url=url)


@router.get("/callback")
def google_callback(code: str, state: str, db: Session = Depends(get_db)):
    try:
        state_payload = _decode_oauth_state(state)
        business_id = int(state_payload["business_id"])
        if not consume_oauth_state(state, business_id, "google_customer", db):
            raise HTTPException(status_code=400, detail="OAuth state has expired or was already used")
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        flow = customer_flow()
        # Google may reorder/expand identity scopes in the callback. The
        # callback is dedicated to identity login, so avoid oauthlib's
        # order-sensitive scope comparison.
        flow.oauth2session.scope = None
        flow.fetch_token(code=code)
        google_id_token = flow.credentials.id_token
        if not google_id_token:
            raise HTTPException(status_code=400, detail="Google did not return an identity token")
        token_info = id_token.verify_oauth2_token(
            google_id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
        if token_info.get("nonce") != state_payload.get("nonce"):
            raise HTTPException(status_code=400, detail="Invalid OAuth nonce")
        if not token_info.get("email_verified"):
            raise HTTPException(status_code=400, detail="Google email is not verified")
        google_id = token_info["sub"]
        customer = db.query(Customer).filter(Customer.business_id == business.id, Customer.google_id == google_id).first()
        if not customer:
            customer = Customer(business_id=business.id, google_id=google_id, email=token_info.get("email"), name=token_info.get("name"))
            db.add(customer)
        else:
            customer.email = token_info.get("email") or customer.email
            customer.name = token_info.get("name") or customer.name
        db.commit()
        customer_token_lifetime = timedelta(minutes=settings.CUSTOMER_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "customer_id": str(customer.id),
                "business_id": business.id,
                "session_version": customer.session_version,
            },
            expires_delta=customer_token_lifetime,
        )
        chat_base = settings.FRONTEND_URL.rstrip("/") or settings.API_BASE_URL.rstrip("/") or "http://localhost:8000"
        response = RedirectResponse(f"{chat_base}/chat?business_key={business.widget_key or ''}")
        response.set_cookie(
            "followly_customer_token",
            access_token,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite="lax",
            max_age=int(customer_token_lifetime.total_seconds()),
        )
        return response
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        import logging
        logging.getLogger(__name__).exception("Customer Google OAuth callback failed")
        raise HTTPException(status_code=400, detail="Unable to sign in with Google") from exc


@router.post("/logout")
def customer_logout(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("followly_customer_token")
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            customer_id = int(payload["customer_id"])
            business_id = int(payload["business_id"])
            customer = db.query(Customer).filter(
                Customer.id == customer_id,
                Customer.business_id == business_id,
            ).first()
            if customer:
                customer.session_version += 1
                db.commit()
        except (ValueError, KeyError, JWTError):
            db.rollback()
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("followly_customer_token")
    response.delete_cookie("followly_visitor_id")
    return response


@router.post("/recover")
def customer_recover(business_key: str, request: Request, db: Session = Depends(get_db)):
    """Revoke the current customer session and restart tenant-scoped Google sign-in."""
    business = db.query(Business).filter(Business.widget_key == business_key).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    token = request.cookies.get("followly_customer_token")
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            customer = db.query(Customer).filter(
                Customer.id == int(payload["customer_id"]),
                Customer.business_id == business.id,
            ).first()
            if customer:
                customer.session_version += 1
                db.commit()
        except (ValueError, KeyError, JWTError):
            db.rollback()
    response = RedirectResponse(url=f"/api/v1/customer/auth/google?business_key={business_key}", status_code=303)
    response.delete_cookie("followly_customer_token")
    return response
