import asyncio
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.models import Base, Appointment, Business, Conversation, Lead, KnowledgeBaseEntry
from app.services.conversation_engine import handle_book_appointment
from app.services.knowledge_service import get_knowledge_entries


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
    start = datetime(2026, 9, 1, 10, 0)
    db.add(Appointment(business_id=first.id, lead_id=first_lead.id, start_time=start, end_time=start + timedelta(hours=1), status="scheduled"))
    db.commit()

    args = {"date": "2026-09-01", "time": "10:00", "service": "cleaning", "patient_name": "New Patient"}
    rejected = asyncio.run(handle_book_appointment(args, first_conversation, first, db))
    allowed = asyncio.run(handle_book_appointment(args, second_conversation, second, db))

    assert rejected["success"] is False
    assert "no longer available" in rejected["error"]
    assert allowed["success"] is True
