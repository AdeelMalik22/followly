from fastapi import APIRouter, Request, Response, HTTPException, Depends, status
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.services import whatsapp_service, conversation_service
from app.services.conversation_engine import process_message_with_agent
from app.schemas.whatsapp import WhatsAppWebhook, WhatsAppCredentialsUpdate, WhatsAppTestMessage
from app.api.dependencies import get_current_business
from app.models.models import Business, LeadStatus, Message
import logging

router = APIRouter(prefix="/api/v1/whatsapp", tags=["whatsapp"])
logger = logging.getLogger(__name__)


@router.get("/status")
async def whatsapp_status(
    business: Business = Depends(get_current_business)
):
    """Return WhatsApp connection status without exposing credentials."""
    try:
        settings_data = business.settings or {}
        return {
            "connected": bool(
                settings_data.get("whatsapp_phone_id")
                and settings_data.get("whatsapp_access_token")
            ),
            "phone_number_id": settings_data.get("whatsapp_phone_id"),
        }
    except Exception:
        logger.exception("Error checking WhatsApp connection status")
        raise HTTPException(status_code=500, detail="Unable to check WhatsApp status")


@router.get("/webhook-url")
async def whatsapp_webhook_url(
    request: Request,
    business: Business = Depends(get_current_business)
):
    """Return the webhook URL to configure in Meta."""
    try:
        base_url = settings.API_BASE_URL.rstrip("/") if settings.API_BASE_URL else str(request.base_url).rstrip("/")
        return {"webhook_url": f"{base_url}/api/v1/whatsapp/webhook"}
    except Exception:
        logger.exception("Error generating WhatsApp webhook URL")
        raise HTTPException(status_code=500, detail="Unable to generate webhook URL")


@router.put("/credentials")
async def update_whatsapp_credentials(
    credentials: WhatsAppCredentialsUpdate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    """Update WhatsApp credentials for the authenticated business."""
    try:
        if not credentials.phone_number_id and not credentials.access_token:
            raise HTTPException(status_code=400, detail="At least one credential is required")

        business.settings = business.settings or {}
        if credentials.phone_number_id is not None:
            business.settings["whatsapp_phone_id"] = credentials.phone_number_id
        if credentials.access_token is not None:
            business.settings["whatsapp_access_token"] = whatsapp_service.encrypt_access_token(
                credentials.access_token
            )
        flag_modified(business, "settings")
        db.commit()
        return {"status": "success", "message": "WhatsApp credentials updated"}
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("Error updating WhatsApp credentials")
        raise HTTPException(status_code=500, detail="Unable to update WhatsApp credentials")


@router.delete("/credentials")
async def remove_whatsapp_credentials(
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    """Remove WhatsApp credentials for the authenticated business."""
    try:
        business.settings = business.settings or {}
        business.settings.pop("whatsapp_phone_id", None)
        business.settings.pop("whatsapp_access_token", None)
        flag_modified(business, "settings")
        db.commit()
        return {"status": "success", "message": "WhatsApp credentials removed"}
    except Exception:
        db.rollback()
        logger.exception("Error removing WhatsApp credentials")
        raise HTTPException(status_code=500, detail="Unable to remove WhatsApp credentials")

@router.get("/webhook")
async def verify_webhook(
    request: Request,
    mode: str = None,
    token: str = None,
    challenge: str = None
):
    """Verify WhatsApp webhook (required by Meta)"""
    try:
        if mode == "subscribe" and token:
            if whatsapp_service.verify_webhook_token(token):
                logger.info("Webhook verified successfully")
                return Response(content=challenge, media_type="text/plain")
            else:
                logger.warning("Webhook verification failed - invalid token")
                raise HTTPException(status_code=403, detail="Verification token mismatch")

        raise HTTPException(status_code=400, detail="Missing parameters")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error verifying WhatsApp webhook")
        raise HTTPException(status_code=500, detail="Unable to verify webhook")

@router.post("/webhook")
async def handle_webhook(
    request: Request,
    webhook_data: dict,
    db: Session = Depends(get_db)
):
    """Handle incoming WhatsApp messages"""
    try:
        app_secret = settings.WHATSAPP_APP_SECRET
        if not app_secret:
            logger.error("WhatsApp app secret is not configured")
            raise HTTPException(status_code=500, detail="WhatsApp webhook not configured")

        signature = request.headers.get("X-Hub-Signature-256")
        payload = await request.body()
        if not whatsapp_service.verify_webhook_signature(payload, signature, app_secret):
            logger.warning("WhatsApp webhook rejected: invalid signature")
            raise HTTPException(status_code=403, detail="Invalid webhook signature")

        # Parse message from webhook
        try:
            parsed = whatsapp_service.parse_whatsapp_message(webhook_data)
        except ValueError as exc:
            logger.warning("Invalid WhatsApp webhook payload: %s", exc)
            raise HTTPException(status_code=400, detail="Invalid WhatsApp webhook payload")

        if not parsed:
            logger.info("WhatsApp status update received, ignoring")
            return {"status": "ok"}

        if not parsed.get("text"):
            logger.info("WhatsApp %s message received without processable text; acknowledging", parsed["message_type"])
            return {"status": "ok"}

        from_number = parsed["from_number"]
        message_text = parsed["text"]
        business_phone_id = parsed["business_phone_id"]
        message_id = parsed.get("message_id")

        if not message_id:
            logger.warning("WhatsApp webhook message has no message ID")
            return {"status": "ok"}

        # Meta may retry webhook deliveries. Check before doing any work so a
        # duplicate cannot trigger another AI response or outbound message.
        if db.query(Message.id).filter(Message.whatsapp_message_id == message_id).first():
            logger.info("Ignoring duplicate WhatsApp message: %s", message_id)
            return {"status": "ok"}

        logger.info(f"Received message from {from_number}: {message_text}")

        # Find business by phone number ID
        business = db.query(Business).filter(
            Business.settings["whatsapp_phone_id"].astext == business_phone_id
        ).first()

        if not business:
            logger.warning(f"No business found for phone ID: {business_phone_id}")
            return {"status": "ok"}

        # Get or create lead
        lead = conversation_service.get_or_create_lead(from_number, business.id, db)

        # Get or create conversation
        conversation = conversation_service.get_or_create_conversation(
            lead.id, business.id, "whatsapp", db
        )

        # Save incoming message
        try:
            conversation_service.save_message(
                conversation.id,
                "user",
                message_text,
                db,
                whatsapp_message_id=message_id
            )
        except IntegrityError:
            # Another concurrent webhook request claimed this message first.
            db.rollback()
            logger.info("Ignoring concurrently duplicated WhatsApp message: %s", message_id)
            return {"status": "ok"}

        # Update lead status to CONTACTED if NEW
        if lead.status == LeadStatus.NEW:
            conversation_service.update_lead_status(lead.id, LeadStatus.CONTACTED, db)

        # Process with AI agent and get response
        agent_response = await process_message_with_agent(conversation, business, message_text, db)

        # Save agent response to database
        conversation_service.save_message(conversation.id, "assistant", agent_response, db)

        # Send response via WhatsApp
        whatsapp_phone_id = business.settings.get("whatsapp_phone_id")
        whatsapp_token = business.settings.get("whatsapp_access_token")
        if whatsapp_token:
            legacy_plaintext = not whatsapp_token.startswith("fernet:")
            whatsapp_token = whatsapp_service.decrypt_access_token(whatsapp_token)
            if legacy_plaintext:
                business.settings["whatsapp_access_token"] = whatsapp_service.encrypt_access_token(whatsapp_token)
                flag_modified(business, "settings")
                db.commit()

        if whatsapp_phone_id and whatsapp_token:
            await whatsapp_service.send_whatsapp_message(
                to=from_number,
                message=agent_response,
                phone_number_id=whatsapp_phone_id,
                access_token=whatsapp_token
            )
            logger.info(f"Agent response sent to {from_number}")
        else:
            logger.warning(f"WhatsApp credentials not found in business settings for {business.id}")

        # Update conversation timestamp
        conversation_service.update_conversation_timestamp(conversation.id, db)

        logger.info(f"Message processed for conversation {conversation.id}")

        return {"status": "ok"}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Error handling webhook: {e}", exc_info=True)
        db.rollback()
        # Return 200 to avoid Meta retrying
        return {"status": "error"}

@router.post("/send")
async def send_message_endpoint(
    to: str,
    message: str,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    """Manual endpoint to send WhatsApp message (for testing)"""
    # This is a test endpoint - in production, messages are sent automatically by the agent

    business_settings = business.settings or {}
    phone_number_id = business_settings.get("whatsapp_phone_id")
    access_token = business_settings.get("whatsapp_access_token")
    if access_token:
        legacy_plaintext = not access_token.startswith("fernet:")
        access_token = whatsapp_service.decrypt_access_token(access_token)
        if legacy_plaintext:
            business.settings["whatsapp_access_token"] = whatsapp_service.encrypt_access_token(access_token)
            flag_modified(business, "settings")
            db.commit()
    if not phone_number_id or not access_token:
        raise HTTPException(status_code=400, detail="WhatsApp credentials not configured")

    try:
        result = await whatsapp_service.send_whatsapp_message(
            to=to,
            message=message,
            phone_number_id=phone_number_id,
            access_token=access_token
        )
        return {"status": "sent", "result": result}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error sending WhatsApp message")
        raise HTTPException(status_code=500, detail="Unable to send message")
