from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.core.database import get_db
from app.core.config import settings
from app.models.models import Business
from app.api.dependencies import get_current_business, get_current_user
from app.services.calendar_service import create_oauth_flow
from app.services.oauth_state_service import consume_oauth_state, store_oauth_state
from app.core.secret_storage import decrypt_json, encrypt_json
import logging

router = APIRouter(prefix="/api/v1/calendar", tags=["calendar"])
logger = logging.getLogger(__name__)


def _create_calendar_state(business_id: int) -> str:
    payload = {
        "business_id": business_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _decode_calendar_state(state: str) -> dict:
    try:
        return jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=400, detail="Invalid calendar OAuth state") from exc

@router.get("/connect")
async def connect_calendar(
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    """Initiate OAuth flow for Google Calendar"""
    try:
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise HTTPException(status_code=500, detail="Google Calendar not configured")

        flow = create_oauth_flow(
            settings.GOOGLE_CLIENT_ID,
            settings.GOOGLE_CLIENT_SECRET,
            settings.GOOGLE_REDIRECT_URI
        )

        # Generate a signed, expiring state containing the tenant identity.
        calendar_state = _create_calendar_state(business.id)
        store_oauth_state(
            calendar_state,
            business.id,
            "google_calendar",
            datetime.now(timezone.utc) + timedelta(minutes=10),
            db,
        )
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=calendar_state
        )

        return {"authorization_url": authorization_url, "state": state}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error initiating calendar connection")
        raise HTTPException(status_code=500, detail="Unable to connect calendar")

@router.get("/callback")
async def calendar_callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
    db: Session = Depends(get_db)
):
    """Handle OAuth callback from Google"""
    if error:
        logger.error(f"Calendar OAuth error: {error}")
        raise HTTPException(status_code=400, detail=f"Authorization failed: {error}")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    try:
        state_payload = _decode_calendar_state(state)
        business_id = int(state_payload["business_id"])
        if not consume_oauth_state(state, business_id, "google_calendar", db):
            raise HTTPException(status_code=400, detail="OAuth state has expired or was already used")
        business = db.query(Business).filter(Business.id == business_id).first()

        if not business:
            raise HTTPException(status_code=404, detail="Business not found")

        # Exchange code for credentials
        flow = create_oauth_flow(
            settings.GOOGLE_CLIENT_ID,
            settings.GOOGLE_CLIENT_SECRET,
            settings.GOOGLE_REDIRECT_URI
        )

        # Google may return OpenID/profile scopes in addition to Calendar when
        # the consent screen is configured with account identity scopes. Tell
        # oauthlib about the scopes returned on the callback so it does not
        # reject an otherwise valid token exchange.
        returned_scopes = request.query_params.get("scope", "").split()
        calendar_scope = "https://www.googleapis.com/auth/calendar"
        if calendar_scope not in returned_scopes:
            raise HTTPException(status_code=400, detail="Calendar permission was not granted")
        # oauthlib compares scope strings in order, while Google is free to
        # return the same scopes in a different order. Calendar permission was
        # verified above, so skip that order-sensitive comparison.
        flow.oauth2session.scope = None

        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Store credentials in business settings
        credentials_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes
        }
        business.google_calendar_credentials = credentials_data
        business.google_calendar_credentials_encrypted = encrypt_json(credentials_data)
        business.settings = business.settings or {}
        business.settings["google_calendar_credentials"] = credentials_data
        flag_modified(business, "settings")

        db.commit()

        logger.info(f"Calendar connected for business {business.id}")

        return RedirectResponse(
            url=f"{settings.FRONTEND_URL.rstrip('/')}/dashboard/channels?calendar=connected"
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error in calendar callback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unable to connect calendar")

@router.get("/status")
async def calendar_status(
    business: Business = Depends(get_current_business)
):
    """Check if calendar is connected"""
    try:
        credentials = None
        if business.google_calendar_credentials_encrypted:
            credentials = decrypt_json(business.google_calendar_credentials_encrypted)
        else:
            credentials = business.google_calendar_credentials or (
                business.settings.get("google_calendar_credentials") if business.settings else None
            )

        return {
            "connected": credentials is not None,
            "business_id": business.id
        }
    except Exception:
        logger.exception("Error checking calendar status")
        raise HTTPException(status_code=500, detail="Unable to check calendar status")

@router.delete("/disconnect")
async def disconnect_calendar(
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    """Disconnect Google Calendar"""
    try:
        business.google_calendar_credentials = None
        business.google_calendar_credentials_encrypted = None
        if business.settings and "google_calendar_credentials" in business.settings:
            del business.settings["google_calendar_credentials"]
            flag_modified(business, "settings")
            db.commit()

        return {"status": "success", "message": "Calendar disconnected"}
    except Exception:
        db.rollback()
        logger.exception("Error disconnecting calendar")
        raise HTTPException(status_code=500, detail="Unable to disconnect calendar")
