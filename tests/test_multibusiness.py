import asyncio
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.models import Base, Appointment, Business, Conversation, ConversationStatus, Lead, LeadStatus, KnowledgeBaseEntry
from app.services.conversation_engine import execute_tool, handle_book_appointment
from app.services.conversation_service import update_conversation_timestamp, update_lead_status
from app.services.knowledge_service import get_knowledge_entries
from app.services.tenant_context import TenantContext


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_knowledge_base_isolated_between_businesses():
    db = make_session()
    first = Business(name="First Clinic", industry="Dental Clinic")
    second = Business(name="Second Clinic", industry="Dental Clinic")
    db.add_all([first, second])
    db.flush()
    db.add_all([
        KnowledgeBaseEntry(business_id=first.id, category="faqs", question="Q1", answer="A1"),
        KnowledgeBaseEntry(business_id=second.id, category="faqs", question="Q2", answer="A2"),
    ])
    db.commit()

    first_entries = get_knowledge_entries(first.id, db=db)
    second_entries = get_knowledge_entries(second.id, db=db)
    assert [entry.question for entry in first_entries] == ["Q1"]
    assert [entry.question for entry in second_entries] == ["Q2"]


def test_deleted_knowledge_is_excluded_from_tenant_retrieval():
    db = make_session()
    business = Business(name="Lifecycle Clinic", industry="Dental Clinic")
    db.add(business)
    db.flush()
    entry = KnowledgeBaseEntry(
        business_id=business.id,
        category="faqs",
        question="Old question",
        answer="Old answer",
        deleted_at=datetime.utcnow(),
    )
    db.add(entry)
    db.commit()

    assert get_knowledge_entries(business.id, db=db) == []


def test_double_booking_rejected_but_other_business_can_book_same_time():
    db = make_session()
    first = Business(name="First Clinic", industry="Dental Clinic", settings={"appointment_duration_minutes": 60})
    second = Business(name="Second Clinic", industry="Dental Clinic", settings={"appointment_duration_minutes": 60})
    db.add_all([first, second])
    db.flush()
    first_lead = Lead(business_id=first.id, phone="111")
    second_lead = Lead(business_id=second.id, phone="222")
    db.add_all([first_lead, second_lead])
    db.flush()
    first_conversation = Conversation(business_id=first.id, lead_id=first_lead.id, channel="web")
    second_conversation = Conversation(business_id=second.id, lead_id=second_lead.id, channel="web")
    db.add_all([first_conversation, second_conversation])
    db.flush()
    start = datetime(2027, 9, 1, 10, 0)
    db.add(Appointment(business_id=first.id, lead_id=first_lead.id, start_time=start, end_time=start + timedelta(hours=1), status="scheduled"))
    db.commit()

    args = {"date": "2027-09-01", "time": "10:00", "service": "cleaning", "patient_name": "New Patient"}
    rejected = asyncio.run(handle_book_appointment(args, first_conversation, first, db))
    allowed = asyncio.run(handle_book_appointment(args, second_conversation, second, db))

    assert rejected["success"] is False
    assert "no longer available" in rejected["error"]
    assert allowed["success"] is True


def test_lead_status_update_requires_matching_business():
    db = make_session()
    first = Business(name="First Clinic", industry="Dental Clinic")
    second = Business(name="Second Clinic", industry="Dental Clinic")
    db.add_all([first, second])
    db.flush()
    lead = Lead(business_id=first.id, phone="111", status=LeadStatus.NEW)
    db.add(lead)
    db.commit()

    update_lead_status(lead.id, second.id, LeadStatus.CONTACTED, db)
    db.refresh(lead)

    assert lead.status == LeadStatus.NEW


def test_conversation_timestamp_update_requires_matching_business():
    db = make_session()
    first = Business(name="First Clinic", industry="Dental Clinic")
    second = Business(name="Second Clinic", industry="Dental Clinic")
    db.add_all([first, second])
    db.flush()
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
    original_timestamp = conversation.last_message_at

    update_conversation_timestamp(conversation.id, second.id, db)
    db.refresh(conversation)

    assert conversation.last_message_at == original_timestamp


def test_agent_tool_rejects_mismatched_business_context():
    db = make_session()
    first = Business(name="First Clinic", industry="Dental Clinic")
    second = Business(name="Second Clinic", industry="Dental Clinic")
    db.add_all([first, second])
    db.flush()
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

    result = asyncio.run(execute_tool("escalate_to_human", {}, conversation, second, db))

    assert result == {"error": "Conversation does not belong to business"}
    db.refresh(conversation)
    assert conversation.status == ConversationStatus.ACTIVE


def test_agent_tool_rejects_explicit_mismatched_tenant_context():
    db = make_session()
    first = Business(name="First Clinic", industry="Dental Clinic")
    second = Business(name="Second Clinic", industry="Dental Clinic")
    db.add_all([first, second])
    db.flush()
    lead = Lead(business_id=first.id, phone="111")
    db.add(lead)
    db.flush()
    conversation = Conversation(business_id=first.id, lead_id=lead.id, channel="web")
    db.add(conversation)
    db.commit()

    result = asyncio.run(execute_tool(
        "escalate_to_human",
        {},
        conversation,
        first,
        db,
        TenantContext(second.id),
    ))

    assert result == {"error": "Business does not belong to tenant context"}
