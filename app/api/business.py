from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
import asyncio
from sqlalchemy.orm import Session
import secrets

from app.api.dependencies import get_current_business, get_current_user, require_business_roles
from app.core.database import get_db
from app.core.config import settings as app_settings
from app.core.config import settings
from app.models.models import Business, User, KnowledgeBaseEntry, ConfigurationAudit, Conversation
from app.schemas.dashboard import (
    BusinessProfileResponse, BusinessProfileUpdate, BookingSettings, BookingSettingsUpdate, WidgetConfigResponse, EscalationSettings,
)
from app.schemas.business_config import BusinessConfiguration, EscalationConfiguration
from app.schemas.test_chat import TestChatRequest, TestChatResponse
from app.services import conversation_service
from app.services.conversation_engine import process_message_with_agent
from app.services.business_config_service import get_business_configuration, save_business_configuration
from app.services.integration_health_service import check_calendar_health, check_whatsapp_health
from app.services.usage_service import enforce_plan_limit, plan_limits
from app.services.tenant_data_service import delete_tenant_data, export_tenant_data
from app.schemas.tenant_data import TenantDeletionRequest

router = APIRouter(prefix="/api/v1/business", tags=["business"])


@router.get("/data-export")
def data_export(
    business: Business = Depends(get_current_business),
    _authorized_user=Depends(require_business_roles("owner")),
    db: Session = Depends(get_db),
):
    return JSONResponse(content=export_tenant_data(business.id, db))


@router.delete("/account")
def delete_account(
    payload: TenantDeletionRequest,
    business: Business = Depends(get_current_business),
    _authorized_user=Depends(require_business_roles("owner")),
    db: Session = Depends(get_db),
):
    if payload.confirmation != business.name:
        raise HTTPException(status_code=400, detail="Confirmation must match the business name")
    delete_tenant_data(business.id, db)
    return {"status": "deleted"}


@router.post("/test-chat", response_model=TestChatResponse)
async def test_chat(
    payload: TestChatRequest,
    business: Business = Depends(get_current_business),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.conversation_id is not None:
        conversation = db.query(Conversation).filter(
            Conversation.id == payload.conversation_id,
            Conversation.business_id == business.id,
            Conversation.channel == "dashboard_test",
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Test conversation not found")
    else:
        lead = conversation_service.get_or_create_lead(
            f"dashboard-test-{user.id}", business.id, db
        )
        lead.source = "dashboard_test"
        db.commit()
        conversation = Conversation(
            lead_id=lead.id,
            business_id=business.id,
            channel="dashboard_test",
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    conversation_service.save_message(conversation.id, business.id, "user", payload.message, db)
    response = await process_message_with_agent(conversation, business, payload.message, db)
    conversation_service.save_message(conversation.id, business.id, "assistant", response, db)
    return TestChatResponse(conversation_id=conversation.id, response=response)


@router.get("/configuration", response_model=BusinessConfiguration)
def get_configuration(business: Business = Depends(get_current_business)):
    return get_business_configuration(business)


@router.put("/configuration", response_model=BusinessConfiguration)
def update_configuration(
    payload: BusinessConfiguration,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
    _authorized_user=Depends(require_business_roles("owner", "admin")),
):
    enabled_channels = sum(1 for enabled in payload.channels.enabled.values() if enabled)
    if enabled_channels > plan_limits(business).get("channels", enabled_channels):
        raise HTTPException(status_code=403, detail="Tenant channels limit reached")
    return save_business_configuration(business, payload, db, updated_by=_authorized_user.id)


@router.get("/configuration/audit")
def configuration_audit_history(
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
    _authorized_user=Depends(require_business_roles("owner", "admin")),
):
    audits = (
        db.query(ConfigurationAudit)
        .filter(ConfigurationAudit.business_id == business.id)
        .order_by(ConfigurationAudit.created_at.desc(), ConfigurationAudit.id.desc())
        .all()
    )
    return [
        {
            "id": audit.id,
            "business_id": audit.business_id,
            "changed_by": audit.changed_by,
            "configuration": audit.configuration,
            "created_at": audit.created_at,
        }
        for audit in audits
    ]


@router.get("/integration-status")
def integration_status(business: Business = Depends(get_current_business)):
    health = business.integration_health or {}
    whatsapp_connected = bool(
        business.whatsapp_phone_id and business.whatsapp_access_token
    )
    calendar_connected = bool(
        business.google_calendar_credentials_encrypted or business.google_calendar_credentials
    )
    return {
        "whatsapp": {
            "connected": whatsapp_connected,
            "status": health.get("whatsapp", {}).get("status", "connected" if whatsapp_connected else "disconnected"),
            "last_error": health.get("whatsapp", {}).get("last_error"),
            "reconnect_required": not whatsapp_connected,
        },
        "calendar": {
            "connected": calendar_connected,
            "status": health.get("calendar", {}).get("status", "connected" if calendar_connected else "disconnected"),
            "last_error": health.get("calendar", {}).get("last_error"),
            "reconnect_required": not calendar_connected,
        },
    }


@router.get("/webhook-metrics")
def webhook_metrics(business: Business = Depends(get_current_business)):
    return business.webhook_metrics or {"received": 0, "processed": 0, "failed": 0, "retried": 0}


@router.get("/integration-health")
async def integration_health(
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    whatsapp, calendar = await asyncio.gather(
        check_whatsapp_health(business),
        check_calendar_health(business),
    )
    business.integration_health = {"whatsapp": whatsapp, "calendar": calendar}
    db.commit()
    return business.integration_health


@router.get("/widget-config", response_model=WidgetConfigResponse)
def get_widget_config(business: Business = Depends(get_current_business), db: Session = Depends(get_db)):
    if not business.widget_key:
        business.widget_key = secrets.token_urlsafe(24)
        db.commit()
    branding = get_business_configuration(business).branding
    embed_code = f'<script src="{app_settings.FRONTEND_URL.rstrip("/")}/widget.js" data-business-key="{business.widget_key}" defer></script>'
    return WidgetConfigResponse(
        widget_key=business.widget_key,
        business_name=business.name,
        embed_code=embed_code,
        primary_color=branding.primary_color,
        logo_url=branding.logo_url,
    )


@router.get("/public-widget-config/{widget_key}", response_model=WidgetConfigResponse)
def get_public_widget_config(widget_key: str, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.widget_key == widget_key).first()
    if not business:
        raise HTTPException(status_code=404, detail="Widget not found")
    branding = get_business_configuration(business).branding
    return WidgetConfigResponse(
        widget_key=business.widget_key,
        business_name=business.name,
        embed_code="",
        primary_color=branding.primary_color,
        logo_url=branding.logo_url,
    )


@router.get("/escalation-settings", response_model=EscalationSettings)
def get_escalation_settings(business: Business = Depends(get_current_business)):
    return EscalationSettings(**get_business_configuration(business).escalation.model_dump())


@router.put("/escalation-settings", response_model=EscalationSettings)
def update_escalation_settings(
    payload: EscalationSettings,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
    _authorized_user=Depends(require_business_roles("owner", "admin")),
):
    configuration = get_business_configuration(business)
    configuration.escalation = EscalationConfiguration.model_validate(payload.model_dump())
    save_business_configuration(business, configuration, db, updated_by=_authorized_user.id)
    return payload


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
        company_size=get_business_configuration(business).business_details.company_size,
        inventory_management=get_business_configuration(business).business_details.inventory_management,
    )


@router.post("/onboarding/complete")
def complete_onboarding(
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
    _authorized_user=Depends(require_business_roles("owner", "admin")),
):
    if not business.name.strip() or not business.industry.strip():
        raise HTTPException(status_code=400, detail="Complete your business profile first")

    entries = db.query(KnowledgeBaseEntry).filter(KnowledgeBaseEntry.business_id == business.id).all()
    categories = {entry.category for entry in entries if entry.question and entry.question.strip() and entry.answer.strip()}
    required_categories = {"services", "pricing", "faqs", "policies"}
    if not required_categories.issubset(categories):
        missing = ", ".join(sorted(required_categories - categories))
        raise HTTPException(status_code=400, detail=f"Complete knowledge-base categories: {missing}")

    configuration = get_business_configuration(business)
    hours = configuration.booking.working_hours
    valid_open_day = False
    for day in hours.values():
        if day.get("open"):
            try:
                from datetime import datetime
                start = datetime.strptime(day.get("start", ""), "%H:%M").time()
                end = datetime.strptime(day.get("end", ""), "%H:%M").time()
                valid_open_day = valid_open_day or start < end
            except (TypeError, ValueError):
                continue
    if not valid_open_day:
        raise HTTPException(status_code=400, detail="Configure at least one valid open business day")

    escalation = configuration.escalation
    if not any((getattr(escalation, key) or "").strip() for key in ("contact_name", "contact_phone", "contact_email", "instructions")):
        raise HTTPException(status_code=400, detail="Configure a human escalation contact or instruction")

    configuration.onboarding_completed = True
    save_business_configuration(business, configuration, db, updated_by=_authorized_user.id)
    return {"status": "completed"}


@router.put("/profile", response_model=BusinessProfileResponse)
def update_profile(
    profile: BusinessProfileUpdate,
    business: Business = Depends(get_current_business),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _authorized_user=Depends(require_business_roles("owner", "admin")),
):
    business.name = profile.name.strip()
    business.industry = profile.industry.strip()
    user.name = profile.owner_name.strip()
    configuration = get_business_configuration(business)
    configuration.business_details.company_size = profile.company_size.strip()
    configuration.business_details.inventory_management = profile.inventory_management
    save_business_configuration(business, configuration, db, updated_by=user.id)
    db.commit()
    db.refresh(business)
    db.refresh(user)
    return BusinessProfileResponse(
        name=business.name,
        industry=business.industry,
        owner_name=user.name,
        owner_email=user.email,
        company_size=configuration.business_details.company_size,
        inventory_management=configuration.business_details.inventory_management,
    )


@router.get("/booking-settings", response_model=BookingSettings)
def get_booking_settings(business: Business = Depends(get_current_business)):
    booking = get_business_configuration(business).booking
    return BookingSettings(
        working_hours=booking.working_hours,
        appointment_duration_minutes=booking.appointment_duration_minutes,
    )


@router.put("/booking-settings", response_model=BookingSettings)
def update_booking_settings(
    payload: BookingSettingsUpdate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
    _authorized_user=Depends(require_business_roles("owner", "admin")),
):
    if not 15 <= payload.appointment_duration_minutes <= 480:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="Appointment duration must be between 15 and 480 minutes")
    configuration = get_business_configuration(business)
    configuration.booking.working_hours = payload.working_hours
    configuration.booking.appointment_duration_minutes = payload.appointment_duration_minutes
    save_business_configuration(business, configuration, db, updated_by=_authorized_user.id)
    return payload
