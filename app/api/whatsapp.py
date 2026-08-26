from fastapi import APIRouter, Request, Response, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services import whatsapp_service, conversation_service
from app.services.conversation_engine import process_message_with_agent
from app.schemas.whatsapp import WhatsAppWebhook
from app.models.models import Business, LeadStatus
import logging

router = APIRouter(prefix="/api/v1/whatsapp", tags=["whatsapp"])
logger = logging.getLogger(__name__)

@router.get("/webhook")
async def verify_webhook(
    request: Request,
    mode: str = None,
    token: str = None,
    challenge: str = None
):
    """Verify WhatsApp webhook (required by Meta)"""
    if mode == "subscribe" and token:
        if whatsapp_service.verify_webhook_token(token):
            logger.info("Webhook verified successfully")
            return Response(content=challenge, media_type="text/plain")
        else:
            logger.warning("Webhook verification failed - invalid token")
            raise HTTPException(status_code=403, detail="Verification token mismatch")

    raise HTTPException(status_code=400, detail="Missing parameters")

@router.post("/webhook")
async def handle_webhook(
    webhook_data: dict,
    db: Session = Depends(get_db)
):
    """Handle incoming WhatsApp messages"""
    try:
        # Parse message from webhook
        parsed = whatsapp_service.parse_whatsapp_message(webhook_data)

        if not parsed or not parsed.get("text"):
            logger.info("Non-text message or status update received, ignoring")
            return {"status": "ok"}

        from_number = parsed["from_number"]
        message_text = parsed["text"]
        business_phone_id = parsed["business_phone_id"]

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
        conversation_service.save_message(conversation.id, "user", message_text, db)

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

    except Exception as e:
        logger.error(f"Error handling webhook: {e}", exc_info=True)
        # Return 200 to avoid Meta retrying
        return {"status": "error", "message": str(e)}

@router.post("/send")
async def send_message_endpoint(
    to: str,
    message: str,
    db: Session = Depends(get_db)
):
    """Manual endpoint to send WhatsApp message (for testing)"""
    # This is a test endpoint - in production, messages are sent automatically by the agent

    from app.core.config import settings

    if not settings.WHATSAPP_PHONE_NUMBER_ID or not settings.WHATSAPP_ACCESS_TOKEN:
        raise HTTPException(status_code=400, detail="WhatsApp credentials not configured")

    try:
        result = await whatsapp_service.send_whatsapp_message(
            to=to,
            message=message,
            phone_number_id=settings.WHATSAPP_PHONE_NUMBER_ID,
            access_token=settings.WHATSAPP_ACCESS_TOKEN
        )
        return {"status": "sent", "result": result}
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))
