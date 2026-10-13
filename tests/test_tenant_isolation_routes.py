import pytest
from fastapi import HTTPException

from app.api import conversations, knowledge, leads
from app.models.models import Business, Conversation, ConversationStatus, Lead, LeadStatus, KnowledgeBaseEntry
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
