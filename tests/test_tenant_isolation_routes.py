import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from app.api import appointments, conversations, knowledge, leads
from app.api.dependencies import get_current_user
from app.core.config import settings
from app.models.models import Appointment, AppointmentStatusHistory, Business, Conversation, ConversationStatus, Lead, LeadStatus, KnowledgeBaseEntry, OAuthState
from app.models.models import User
from app.schemas.dashboard import AppointmentUpdate
from app.services.oauth_state_service import consume_oauth_state, store_oauth_state
from app.services.whatsapp_service import decrypt_access_token, encrypt_access_token
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
