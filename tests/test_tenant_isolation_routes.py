import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from app.api import conversations, knowledge, leads
from app.api.dependencies import get_current_user
from app.core.config import settings
from app.models.models import Business, Conversation, ConversationStatus, Lead, LeadStatus, KnowledgeBaseEntry, OAuthState
from app.models.models import User
from app.services.oauth_state_service import consume_oauth_state, store_oauth_state
from app.services.whatsapp_service import decrypt_access_token, encrypt_access_token
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
