import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from app.api import analytics, appointments, billing, business, conversations, follow_up_rules, knowledge, leads
from app.services import agent_service, tenant_cache_service
from app.main import app
from app.api.dependencies import get_current_user, require_business_roles
from app.core.config import settings
from app.models.models import Appointment, AppointmentStatusHistory, Business, Conversation, ConversationStatus, FollowUpRule, Lead, LeadStatus, KnowledgeBaseEntry, OAuthState, WebhookEvent
from app.models.models import User
from app.schemas.dashboard import AppointmentUpdate, FollowUpRuleUpdate
from app.services.oauth_state_service import consume_oauth_state, store_oauth_state
from app.services.tenant_context import TenantContext, knowledge_cache_key, prompt_cache_key
from app.services.webhook_event_service import claim_webhook_event, complete_webhook_event, recover_stale_webhook_events
from app.services.whatsapp_service import decrypt_access_token, encrypt_access_token
from app.services.whatsapp_service import parse_whatsapp_message, verify_webhook_signature
from app.core.secret_storage import decrypt_json, encrypt_json
from app.schemas.dashboard import LeadUpdate
from app.schemas.knowledge import KnowledgeBaseUpdate

from tests.test_multibusiness import make_session


def make_two_businesses(db):
    first = Business(name="First Clinic", industry="Dental Clinic")
    second = Business(name="Second Clinic", industry="Dental Clinic")
    db.add_all([first, second])
    db.flush()
    return first, second


def test_knowledge_route_hides_entry_from_other_business():
    db = make_session()
    first, second = make_two_businesses(db)
    entry = KnowledgeBaseEntry(
        business_id=first.id,
        category="faqs",
        question="Private question",
        answer="Private answer",
    )
    db.add(entry)
    db.commit()

    with pytest.raises(HTTPException) as error:
        knowledge.get_entry(entry.id, second, db)

    assert error.value.status_code == 404


def test_knowledge_route_cannot_update_other_business_entry():
    db = make_session()
    first, second = make_two_businesses(db)
    entry = KnowledgeBaseEntry(
        business_id=first.id,
        category="faqs",
        question="Private question",
        answer="Private answer",
    )
    db.add(entry)
    db.commit()

    with pytest.raises(HTTPException) as error:
        knowledge.update_entry(
            entry.id,
            KnowledgeBaseUpdate(answer="Changed answer"),
            second,
            db,
        )

    db.refresh(entry)
    assert error.value.status_code == 404
    assert entry.answer == "Private answer"


def test_lead_route_hides_lead_from_other_business():
    db = make_session()
    first, second = make_two_businesses(db)
    lead = Lead(business_id=first.id, phone="111", status=LeadStatus.NEW)
    db.add(lead)
    db.commit()

    with pytest.raises(HTTPException) as error:
        leads.update_lead(lead.id, LeadUpdate(status=LeadStatus.CONTACTED), second, db)

    db.refresh(lead)
    assert error.value.status_code == 404
    assert lead.status == LeadStatus.NEW


def test_conversation_route_hides_conversation_from_other_business():
    db = make_session()
    first, second = make_two_businesses(db)
    lead = Lead(business_id=first.id, phone="111")
    db.add(lead)
    db.flush()
    conversation = Conversation(
        business_id=first.id,
        lead_id=lead.id,
        channel="web",
        status=ConversationStatus.ACTIVE,
    )
    db.add(conversation)
    db.commit()

    with pytest.raises(HTTPException) as error:
        conversations.get_conversation(conversation.id, second, db)

    assert error.value.status_code == 404


def test_business_user_rejects_mismatched_tenant_claim():
    db = make_session()
    first, second = make_two_businesses(db)
    user = User(
        business_id=first.id,
        email="owner@example.com",
        name="Owner",
        hashed_password="not-used",
    )
    db.add(user)
    db.commit()
    token = jwt.encode(
        {"sub": str(user.id), "business_id": second.id},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    with pytest.raises(HTTPException) as error:
        get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token), db)

    assert error.value.status_code == 401


def test_sensitive_business_dependency_requires_owner_or_admin():
    db = make_session()
    business, _ = make_two_businesses(db)
    staff = User(
        business_id=business.id,
        email="staff@example.com",
        name="Staff",
        role="staff",
        hashed_password="not-used",
    )
    db.add(staff)
    db.commit()

    with pytest.raises(HTTPException) as error:
        require_business_roles("owner", "admin")(staff)

    assert error.value.status_code == 403


def test_billing_checkout_requires_sensitive_business_role():
    checkout_route = next(route for route in billing.router.routes if route.path.endswith("/checkout"))
    role_dependency = next(
        dependency.call
        for dependency in checkout_route.dependant.dependencies
        if dependency.call.__name__ == "role_dependency"
    )
    db = make_session()
    business, _ = make_two_businesses(db)
    staff = User(
        business_id=business.id,
        email="billing-staff@example.com",
        name="Billing Staff",
        role="staff",
        hashed_password="not-used",
    )
    db.add(staff)
    db.commit()

    with pytest.raises(HTTPException) as error:
        role_dependency(staff)

    assert error.value.status_code == 403


def test_business_profile_update_requires_sensitive_business_role():
    profile_route = next(route for route in business.router.routes if route.path.endswith("/profile") and "PUT" in route.methods)
    role_dependency = next(
        dependency.call
        for dependency in profile_route.dependant.dependencies
        if dependency.call.__name__ == "role_dependency"
    )
    db = make_session()
    tenant, _ = make_two_businesses(db)
    staff = User(
        business_id=tenant.id,
        email="profile-staff@example.com",
        name="Profile Staff",
        role="staff",
        hashed_password="not-used",
    )
    db.add(staff)
    db.commit()

    with pytest.raises(HTTPException) as error:
        role_dependency(staff)

    assert error.value.status_code == 403


def test_booking_settings_update_requires_sensitive_business_role():
    booking_route = next(route for route in business.router.routes if route.path.endswith("/booking-settings") and "PUT" in route.methods)
    role_dependency = next(
        dependency.call
        for dependency in booking_route.dependant.dependencies
        if dependency.call.__name__ == "role_dependency"
    )
    db = make_session()
    tenant, _ = make_two_businesses(db)
    staff = User(
        business_id=tenant.id,
        email="booking-staff@example.com",
        name="Booking Staff",
        role="staff",
        hashed_password="not-used",
    )
    db.add(staff)
    db.commit()

    with pytest.raises(HTTPException) as error:
        role_dependency(staff)

    assert error.value.status_code == 403


def test_escalation_settings_update_requires_sensitive_business_role():
    escalation_route = next(route for route in business.router.routes if route.path.endswith("/escalation-settings") and "PUT" in route.methods)
    role_dependency = next(
        dependency.call
        for dependency in escalation_route.dependant.dependencies
        if dependency.call.__name__ == "role_dependency"
    )
    db = make_session()
    tenant, _ = make_two_businesses(db)
    staff = User(
        business_id=tenant.id,
        email="escalation-staff@example.com",
        name="Escalation Staff",
        role="staff",
        hashed_password="not-used",
    )
    db.add(staff)
    db.commit()

    with pytest.raises(HTTPException) as error:
        role_dependency(staff)

    assert error.value.status_code == 403


def test_onboarding_completion_requires_sensitive_business_role():
    onboarding_route = next(route for route in business.router.routes if route.path.endswith("/onboarding/complete"))
    role_dependency = next(
        dependency.call
        for dependency in onboarding_route.dependant.dependencies
        if dependency.call.__name__ == "role_dependency"
    )
    db = make_session()
    tenant, _ = make_two_businesses(db)
    staff = User(
        business_id=tenant.id,
        email="onboarding-staff@example.com",
        name="Onboarding Staff",
        role="staff",
        hashed_password="not-used",
    )
    db.add(staff)
    db.commit()

    with pytest.raises(HTTPException) as error:
        role_dependency(staff)

    assert error.value.status_code == 403


def test_analytics_summary_is_tenant_scoped():
    db = make_session()
    first, second = make_two_businesses(db)
    db.add_all([
        Lead(business_id=first.id, phone="analytics-first", status=LeadStatus.NEW),
        Lead(business_id=second.id, phone="analytics-second", status=LeadStatus.NEW),
    ])
    db.commit()

    summary = analytics.get_analytics_summary(days=30, business=first, db=db)

    assert summary.funnel.total_leads == 1


def test_follow_up_rule_id_lookups_are_tenant_scoped():
    db = make_session()
    first, second = make_two_businesses(db)
    rule = FollowUpRule(
        business_id=first.id,
        trigger_condition="new_lead",
        delay_hours=24,
        message_template="Follow up",
        active=1,
        created_at=datetime.utcnow(),
    )
    db.add(rule)
    db.commit()

    with pytest.raises(HTTPException) as error:
        follow_up_rules.update_rule(
            rule.id,
            FollowUpRuleUpdate(message_template="Cross-tenant update"),
            second,
            db,
        )

    db.refresh(rule)
    assert error.value.status_code == 404
    assert rule.message_template == "Follow up"


def test_follow_up_rule_mutations_require_sensitive_business_role():
    mutation_routes = [
        route for route in follow_up_rules.router.routes
        if (route.path.endswith("/follow-up-rules") or route.path.endswith("/follow-up-rules/{rule_id}")) and route.methods & {"POST", "PUT", "DELETE"}
    ]
    assert len(mutation_routes) == 3
    db = make_session()
    tenant, _ = make_two_businesses(db)
    staff = User(
        business_id=tenant.id,
        email="follow-up-staff@example.com",
        name="Follow-up Staff",
        role="staff",
        hashed_password="not-used",
    )
    db.add(staff)
    db.commit()

    for route in mutation_routes:
        role_dependency = next(
            dependency.call
            for dependency in route.dependant.dependencies
            if dependency.call.__name__ == "role_dependency"
        )
        with pytest.raises(HTTPException) as error:
            role_dependency(staff)
        assert error.value.status_code == 403


def test_oauth_state_is_single_use_and_business_scoped():
    db = make_session()
    first, second = make_two_businesses(db)
    state = "signed-state-value"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    store_oauth_state(state, first.id, "google_customer", expires_at, db)

    assert consume_oauth_state(state, first.id, "google_customer", db) is True
    assert consume_oauth_state(state, first.id, "google_customer", db) is False
    assert consume_oauth_state(state, second.id, "google_customer", db) is False


def test_whatsapp_phone_id_resolves_to_one_business():
    db = make_session()
    first, second = make_two_businesses(db)
    first.whatsapp_phone_id = "phone-first"
    second.whatsapp_phone_id = "phone-second"
    db.commit()

    resolved = db.query(Business).filter(Business.whatsapp_phone_id == "phone-second").first()

    assert resolved is second


def test_duplicate_whatsapp_phone_id_is_rejected():
    db = make_session()
    first, second = make_two_businesses(db)
    first.whatsapp_phone_id = "phone-shared"
    second.whatsapp_phone_id = "phone-shared"

    with pytest.raises(IntegrityError):
        db.commit()


def test_storing_oauth_state_prunes_expired_states():
    db = make_session()
    first, _ = make_two_businesses(db)
    store_oauth_state(
        "expired-state",
        first.id,
        "google_customer",
        datetime.now(timezone.utc) - timedelta(minutes=1),
        db,
    )

    store_oauth_state(
        "active-state",
        first.id,
        "google_customer",
        datetime.now(timezone.utc) + timedelta(minutes=10),
        db,
    )

    assert db.query(OAuthState).filter(OAuthState.state_hash != "").count() == 1


def test_whatsapp_credentials_are_encrypted_and_business_scoped():
    db = make_session()
    first, second = make_two_businesses(db)
    first.whatsapp_phone_id = "phone-first"
    first.whatsapp_access_token = encrypt_access_token("token-first")
    second.whatsapp_phone_id = "phone-second"
    second.whatsapp_access_token = encrypt_access_token("token-second")
    db.commit()

    db.refresh(first)
    db.refresh(second)
    assert first.whatsapp_access_token != second.whatsapp_access_token
    assert first.whatsapp_access_token.startswith("fernet:")
    assert second.whatsapp_access_token.startswith("fernet:")
    assert decrypt_access_token(first.whatsapp_access_token) == "token-first"
    assert decrypt_access_token(second.whatsapp_access_token) == "token-second"


def test_calendar_credentials_can_be_encrypted_and_decrypted():
    credentials = {"refresh_token": "refresh-first", "client_secret": "secret-first"}
    encrypted = encrypt_json(credentials)

    assert encrypted != str(credentials)
    assert decrypt_json(encrypted) == credentials


def test_appointment_status_update_is_tenant_scoped():
    db = make_session()
    first, second = make_two_businesses(db)
    lead = Lead(business_id=first.id, phone="111")
    db.add(lead)
    db.flush()
    appointment = Appointment(
        business_id=first.id,
        lead_id=lead.id,
        start_time=datetime(2027, 1, 1, 10, 0),
        end_time=datetime(2027, 1, 1, 11, 0),
        status="scheduled",
    )
    db.add(appointment)
    db.commit()

    updated = appointments.update_appointment(
        appointment.id,
        AppointmentUpdate(status="completed"),
        first,
        db,
    )
    assert updated.status == "completed"
    history = db.query(AppointmentStatusHistory).filter(
        AppointmentStatusHistory.appointment_id == appointment.id
    ).one()
    assert history.business_id == first.id
    assert history.previous_status == "scheduled"
    assert history.new_status == "completed"
    history_response = appointments.get_appointment_history(appointment.id, 0, 50, first, db)
    assert len(history_response) == 1
    assert history_response[0].new_status == "completed"

    appointments.update_appointment(
        appointment.id,
        AppointmentUpdate(status="completed"),
        first,
        db,
    )
    paged_history = appointments.get_appointment_history(appointment.id, 1, 1, first, db)
    assert len(paged_history) == 1
    assert paged_history[0].previous_status == "completed"

    fetched = appointments.get_appointment(appointment.id, first, db)
    assert fetched.id == appointment.id
    assert fetched.status == "completed"

    with pytest.raises(HTTPException) as error:
        appointments.get_appointment(appointment.id, second, db)
    assert error.value.status_code == 404

    with pytest.raises(HTTPException) as error:
        appointments.update_appointment(
            appointment.id,
            AppointmentUpdate(status="cancelled"),
            second,
            db,
        )
    assert error.value.status_code == 404

    with pytest.raises(HTTPException) as error:
        appointments.get_appointment_history(appointment.id, 0, 50, second, db)
    assert error.value.status_code == 404


def test_appointment_status_update_rejects_unknown_status():
    db = make_session()
    first, _ = make_two_businesses(db)

    with pytest.raises(HTTPException) as error:
        appointments.update_appointment(
            1,
            AppointmentUpdate(status="unknown"),
            first,
            db,
        )
    assert error.value.status_code == 422


def test_appointment_list_rejects_unknown_status():
    db = make_session()
    first, _ = make_two_businesses(db)

    with pytest.raises(HTTPException) as error:
        appointments.list_appointments("pending", 0, 50, first, db)

    assert error.value.status_code == 422


def test_appointment_list_rejects_reversed_date_range():
    db = make_session()
    first, _ = make_two_businesses(db)

    with pytest.raises(HTTPException) as error:
        appointments.list_appointments(
            None,
            None,
            None,
            None,
            None,
            datetime(2027, 2, 1, 10, 0),
            datetime(2027, 1, 1, 10, 0),
            0,
            50,
            first,
            db,
        )

    assert error.value.status_code == 422


def test_appointment_list_scopes_lead_filter_to_business():
    db = make_session()
    first, second = make_two_businesses(db)
    first_lead = Lead(business_id=first.id, phone="111")
    second_lead = Lead(business_id=second.id, phone="222")
    db.add_all([first_lead, second_lead])
    db.flush()
    db.add_all([
        Appointment(
            business_id=first.id,
            lead_id=first_lead.id,
            start_time=datetime(2027, 1, 1, 10, 0),
            end_time=datetime(2027, 1, 1, 11, 0),
            status="scheduled",
        ),
        Appointment(
            business_id=second.id,
            lead_id=second_lead.id,
            start_time=datetime(2027, 1, 1, 10, 0),
            end_time=datetime(2027, 1, 1, 11, 0),
            status="scheduled",
        ),
    ])
    db.commit()

    appointments_for_first = appointments.list_appointments(
        None, first_lead.id, None, None, "desc", None, None, 0, 50, first, db
    )

    assert len(appointments_for_first) == 1
    assert appointments_for_first[0].business_id == first.id
    assert appointments_for_first[0].lead_id == first_lead.id


def test_appointment_list_applies_date_range_filters():
    db = make_session()
    first, _ = make_two_businesses(db)
    lead = Lead(business_id=first.id, phone="111")
    db.add(lead)
    db.flush()
    db.add_all([
        Appointment(
            business_id=first.id,
            lead_id=lead.id,
            start_time=datetime(2027, 1, 1, 10, 0),
            end_time=datetime(2027, 1, 1, 11, 0),
            status="scheduled",
        ),
        Appointment(
            business_id=first.id,
            lead_id=lead.id,
            start_time=datetime(2027, 2, 1, 10, 0),
            end_time=datetime(2027, 2, 1, 11, 0),
            status="scheduled",
        ),
    ])
    db.commit()

    filtered = appointments.list_appointments(
        None,
        None,
        None,
        None,
        "desc",
        datetime(2027, 1, 15),
        datetime(2027, 1, 31),
        0,
        50,
        first,
        db,
    )

    assert filtered == []


def test_appointment_status_cannot_reopen_terminal_appointment():
    db = make_session()
    first, _ = make_two_businesses(db)
    lead = Lead(business_id=first.id, phone="111")
    db.add(lead)
    db.flush()
    appointment = Appointment(
        business_id=first.id,
        lead_id=lead.id,
        start_time=datetime(2027, 1, 1, 10, 0),
        end_time=datetime(2027, 1, 1, 11, 0),
        status="completed",
    )
    db.add(appointment)
    db.commit()

    with pytest.raises(HTTPException) as error:
        appointments.update_appointment(
            appointment.id,
            AppointmentUpdate(status="scheduled"),
            first,
            db,
        )

    assert error.value.status_code == 409


def test_appointment_list_search_is_tenant_scoped():
    db = make_session()
    first, second = make_two_businesses(db)
    first_lead = Lead(business_id=first.id, phone="111", name="Alex First")
    second_lead = Lead(business_id=second.id, phone="222", name="Alex Second")
    db.add_all([first_lead, second_lead])
    db.flush()
    db.add_all([
        Appointment(
            business_id=first.id,
            lead_id=first_lead.id,
            start_time=datetime(2027, 1, 1, 10, 0),
            end_time=datetime(2027, 1, 1, 11, 0),
            status="scheduled",
        ),
        Appointment(
            business_id=second.id,
            lead_id=second_lead.id,
            start_time=datetime(2027, 1, 1, 10, 0),
            end_time=datetime(2027, 1, 1, 11, 0),
            status="scheduled",
        ),
    ])
    db.commit()

    results = appointments.list_appointments(
        None, None, "Alex", None, "desc", None, None, 0, 50, first, db
    )

    assert len(results) == 1
    assert results[0].business_id == first.id
    assert results[0].lead_id == first_lead.id


def test_appointment_list_filters_by_service_within_business():
    db = make_session()
    first, _ = make_two_businesses(db)
    lead = Lead(business_id=first.id, phone="111")
    db.add(lead)
    db.flush()
    db.add_all([
        Appointment(
            business_id=first.id,
            lead_id=lead.id,
            start_time=datetime(2027, 1, 1, 10, 0),
            end_time=datetime(2027, 1, 1, 11, 0),
            service="Teeth Cleaning",
            status="scheduled",
        ),
        Appointment(
            business_id=first.id,
            lead_id=lead.id,
            start_time=datetime(2027, 1, 2, 10, 0),
            end_time=datetime(2027, 1, 2, 11, 0),
            service="Whitening",
            status="scheduled",
        ),
    ])
    db.commit()

    results = appointments.list_appointments(
        None, None, None, "cleaning", "desc", None, None, 0, 50, first, db
    )

    assert len(results) == 1
    assert results[0].service == "Teeth Cleaning"


def test_appointment_summary_is_tenant_scoped():
    db = make_session()
    first, second = make_two_businesses(db)
    first_lead = Lead(business_id=first.id, phone="111")
    second_lead = Lead(business_id=second.id, phone="222")
    db.add_all([first_lead, second_lead])
    db.flush()
    db.add_all([
        Appointment(
            business_id=first.id,
            lead_id=first_lead.id,
            start_time=datetime(2027, 1, 1, 10, 0),
            end_time=datetime(2027, 1, 1, 11, 0),
            status="scheduled",
        ),
        Appointment(
            business_id=first.id,
            lead_id=first_lead.id,
            start_time=datetime(2027, 1, 2, 10, 0),
            end_time=datetime(2027, 1, 2, 11, 0),
            status="completed",
        ),
        Appointment(
            business_id=second.id,
            lead_id=second_lead.id,
            start_time=datetime(2027, 1, 1, 10, 0),
            end_time=datetime(2027, 1, 1, 11, 0),
            status="cancelled",
        ),
    ])
    db.commit()

    summary = appointments.appointment_summary(None, None, first, db)

    assert summary == {
        "scheduled": 1,
        "completed": 1,
        "no_show": 0,
        "cancelled": 0,
    }


def test_appointment_summary_applies_date_range():
    db = make_session()
    first, _ = make_two_businesses(db)
    lead = Lead(business_id=first.id, phone="111")
    db.add(lead)
    db.flush()
    db.add_all([
        Appointment(
            business_id=first.id,
            lead_id=lead.id,
            start_time=datetime(2027, 1, 1, 10, 0),
            end_time=datetime(2027, 1, 1, 11, 0),
            status="scheduled",
        ),
        Appointment(
            business_id=first.id,
            lead_id=lead.id,
            start_time=datetime(2027, 2, 1, 10, 0),
            end_time=datetime(2027, 2, 1, 11, 0),
            status="completed",
        ),
    ])
    db.commit()

    summary = appointments.appointment_summary(
        datetime(2027, 1, 1), datetime(2027, 1, 31), first, db
    )

    assert summary == {
        "scheduled": 1,
        "completed": 0,
        "no_show": 0,
        "cancelled": 0,
    }


def test_appointment_list_supports_ascending_sort():
    db = make_session()
    first, _ = make_two_businesses(db)
    lead = Lead(business_id=first.id, phone="111")
    db.add(lead)
    db.flush()
    db.add_all([
        Appointment(
            business_id=first.id,
            lead_id=lead.id,
            start_time=datetime(2027, 2, 1, 10, 0),
            end_time=datetime(2027, 2, 1, 11, 0),
            status="scheduled",
        ),
        Appointment(
            business_id=first.id,
            lead_id=lead.id,
            start_time=datetime(2027, 1, 1, 10, 0),
            end_time=datetime(2027, 1, 1, 11, 0),
            status="scheduled",
        ),
    ])
    db.commit()

    results = appointments.list_appointments(
        None, None, None, None, "asc", None, None, 0, 50, first, db
    )

    assert [item.start_time.month for item in results] == [1, 2]


def test_business_owned_routes_require_tenant_context():
    protected_prefixes = (
        "/api/v1/knowledge",
        "/api/v1/whatsapp/status",
        "/api/v1/whatsapp/webhook-url",
        "/api/v1/whatsapp/credentials",
        "/api/v1/whatsapp/send",
        "/api/v1/calendar/status",
        "/api/v1/calendar/connect",
        "/api/v1/calendar/disconnect",
        "/api/v1/conversations",
        "/api/v1/leads",
        "/api/v1/appointments",
        "/api/v1/analytics",
        "/api/v1/follow-up-rules",
        "/api/v1/business",
        "/api/v1/billing",
    )

    def dependency_names(dependant):
        names = {getattr(dependant.call, "__name__", None)}
        for child in dependant.dependencies:
            names.update(dependency_names(child))
        return names

    business_routes = [
        route for route in app.routes
        if getattr(route, "path", "").startswith(protected_prefixes)
        and not getattr(route, "path", "").startswith("/api/v1/business/public-widget-config")
    ]
    assert business_routes
    missing = [
        f"{sorted(route.methods)} {route.path}"
        for route in business_routes
        if "get_current_business" not in dependency_names(route.dependant)
    ]
    assert missing == []


def test_agent_context_and_cache_keys_are_tenant_scoped():
    first_context = TenantContext(101)
    second_context = TenantContext(202)

    assert knowledge_cache_key(first_context) != knowledge_cache_key(second_context)
    assert prompt_cache_key(first_context) != prompt_cache_key(second_context)


def test_prompt_configuration_isolation():
    db = make_session()
    first, second = make_two_businesses(db)
    first.configuration = {"agent": {"tone": "formal", "language": "fr", "instructions": "First tenant instruction"}}
    second.configuration = {"agent": {"tone": "casual", "language": "es", "instructions": "Second tenant instruction"}}
    db.commit()

    first_prompt = agent_service.build_system_prompt(first, db)
    second_prompt = agent_service.build_system_prompt(second, db)

    assert "First tenant instruction" in first_prompt
    assert "Second tenant instruction" not in first_prompt
    assert "Second tenant instruction" in second_prompt
    assert "First tenant instruction" not in second_prompt


def test_tenant_cache_hits_cannot_cross_businesses(monkeypatch):
    values = {}

    class FakeRedis:
        def get(self, key):
            return values.get(key)

        def setex(self, key, ttl, value):
            values[key] = value

        def delete(self, key):
            values.pop(key, None)

    monkeypatch.setattr(tenant_cache_service, "_client", FakeRedis())
    first_context = TenantContext(101)
    second_context = TenantContext(202)

    assert tenant_cache_service.set_cached(first_context, "prompt", {"value": "first"}) is True
    assert tenant_cache_service.get_cached(first_context, "prompt") == {"value": "first"}
    assert tenant_cache_service.get_cached(second_context, "prompt") is None


def test_failed_webhook_event_can_be_reclaimed_but_processed_event_cannot():
    db = make_session()
    first, _ = make_two_businesses(db)

    assert claim_webhook_event(first.id, "whatsapp", "evt-1", db) is True
    complete_webhook_event(first.id, "whatsapp", "evt-1", db, error="temporary failure")
    assert claim_webhook_event(first.id, "whatsapp", "evt-1", db) is True
    complete_webhook_event(first.id, "whatsapp", "evt-1", db)
    assert claim_webhook_event(first.id, "whatsapp", "evt-1", db) is False

    event = db.query(WebhookEvent).filter(WebhookEvent.event_id == "evt-1").one()
    assert event.status == "processed"


def test_webhook_signature_rejects_missing_tampered_and_malformed_signatures():
    import hashlib
    import hmac

    payload = b'{"object":"whatsapp_business_account"}'
    secret = "app-secret"
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    assert verify_webhook_signature(payload, f"sha256={digest}", secret) is True
    assert verify_webhook_signature(payload + b"x", f"sha256={digest}", secret) is False
    assert verify_webhook_signature(payload, digest, secret) is False
    assert verify_webhook_signature(payload, None, secret) is False


def test_webhook_payload_preserves_tenant_routing_identifier():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{"changes": [{"value": {
            "metadata": {"phone_number_id": "phone-tenant-a"},
            "messages": [{
                "id": "wamid-1",
                "from": "15551234567",
                "timestamp": "1700000000",
                "type": "text",
                "text": {"body": "Hello"},
            }],
        }}]}],
    }

    parsed = parse_whatsapp_message(payload)

    assert parsed["business_phone_id"] == "phone-tenant-a"
    assert parsed["message_id"] == "wamid-1"


def test_stale_webhook_processing_claims_are_recoverable():
    db = make_session()
    first, _ = make_two_businesses(db)
    event = WebhookEvent(
        business_id=first.id,
        provider="whatsapp",
        event_id="stale-event",
        status="processing",
        received_at=datetime.utcnow() - timedelta(minutes=30),
    )
    db.add(event)
    db.commit()

    assert recover_stale_webhook_events(db, timeout_minutes=15) == 1
    db.refresh(event)
    assert event.status == "failed"
    assert claim_webhook_event(first.id, "whatsapp", "stale-event", db) is True
