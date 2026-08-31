from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.core.database import get_db
from app.core.config import settings
from app.models.models import Business
from app.api.dependencies import get_current_business, get_current_user
from app.services.calendar_service import create_oauth_flow
import logging

router = APIRouter(prefix="/api/v1/calendar", tags=["calendar"])
logger = logging.getLogger(__name__)

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

        # Generate authorization URL with state containing business_id
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=str(business.id)
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
        business_id = int(state)
        business = db.query(Business).filter(Business.id == business_id).first()

        if not business:
            raise HTTPException(status_code=404, detail="Business not found")

        # Exchange code for credentials
        flow = create_oauth_flow(
            settings.GOOGLE_CLIENT_ID,
            settings.GOOGLE_CLIENT_SECRET,
            settings.GOOGLE_REDIRECT_URI
        )

        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Store credentials in business settings
        business.settings = business.settings or {}
        business.settings["google_calendar_credentials"] = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes
        }
        flag_modified(business, "settings")

        db.commit()

        logger.info(f"Calendar connected for business {business.id}")

        return {
            "status": "success",
            "message": "Google Calendar connected successfully",
            "business_id": business.id
        }

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
        credentials = business.settings.get("google_calendar_credentials") if business.settings else None

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
        if business.settings and "google_calendar_credentials" in business.settings:
            del business.settings["google_calendar_credentials"]
            flag_modified(business, "settings")
            db.commit()

        return {"status": "success", "message": "Calendar disconnected"}
    except Exception:
        db.rollback()
        logger.exception("Error disconnecting calendar")
        raise HTTPException(status_code=500, detail="Unable to disconnect calendar")
