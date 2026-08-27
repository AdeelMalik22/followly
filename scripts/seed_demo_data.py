"""Seed one realistic, synthetic dataset for local agent testing."""

from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.models import (
    Appointment, Business, Conversation, ConversationStatus, FollowUpRule,
    KnowledgeBaseEntry, Lead, LeadStatus, Message, ToolCallAudit, User,
)

BUSINESS_NAME = "Adeel Dental Clinic"
ADMIN_EMAIL = "admin@adeeldentalclinic.com"
LEGACY_ADMIN_EMAIL = "admin@adeeldental.test"
ADMIN_PASSWORD = "AdeelDental123!"


def seed() -> None:
    db = SessionLocal()
    try:
        business = db.query(Business).filter(Business.name == BUSINESS_NAME).first()
        if not business:
            business = Business(
                name=BUSINESS_NAME,
                settings={
                    "address": "12 Main Boulevard, Lahore",
                    "phone": "+923001234567",
                    "whatsapp_phone_id": "demo-phone-id",
                },
            )
            db.add(business)
            db.flush()

        admin = db.query(User).filter(User.email.in_([ADMIN_EMAIL, LEGACY_ADMIN_EMAIL])).first()
        if admin and admin.email == LEGACY_ADMIN_EMAIL:
            admin.email = ADMIN_EMAIL
        if not admin:
            db.add(User(
                business_id=business.id, email=ADMIN_EMAIL,
                name="Adeel Clinic Owner",
                hashed_password=get_password_hash(ADMIN_PASSWORD), role="owner",
            ))
        for i in range(99):
            email = f"staff{i + 1}@adeeldental.test"
            if not db.query(User).filter(User.email == email).first():
                db.add(User(
                    business_id=business.id, email=email,
                    name=f"Demo Staff {i + 1}",
                    hashed_password=get_password_hash("AdeelStaff123!"),
                    role="agent" if i % 3 else "admin",
                ))

        for i in range(100):
            email = f"patient{i + 1}@example.test"
            lead = db.query(Lead).filter(
                Lead.business_id == business.id, Lead.email == email
            ).first()
            if not lead:
                statuses = list(LeadStatus)
                lead = Lead(
                    business_id=business.id, phone=f"92300100{i:04d}",
                    name=f"Test Patient {i + 1}", email=email,
                    status=statuses[i % len(statuses)], source="demo_seed",
                    last_contact_at=datetime.utcnow() - timedelta(days=i % 30),
                )
                db.add(lead)
                db.flush()

            conversation = Conversation(
                business_id=business.id, lead_id=lead.id, channel="web",
                status=ConversationStatus.ACTIVE,
                last_message_at=datetime.utcnow() - timedelta(hours=i),
            )
            db.add(conversation)
            db.flush()

            db.add(Message(
                conversation_id=conversation.id, role="user",
                content=[
                    "I would like to book a dental cleaning.",
                    "How much does a whitening consultation cost?",
                    "Can I reschedule my appointment?",
                    "I have a question about your clinic hours.",
                ][i % 4],
                timestamp=datetime.utcnow() - timedelta(hours=i),
                # Seed messages are not inbound webhook deliveries; leave the
                # id unset so rerunning the script cannot collide with the
                # unique WhatsApp idempotency index.
                whatsapp_message_id=None,
            ))

            appointment = Appointment(
                business_id=business.id, lead_id=lead.id,
                start_time=datetime.utcnow() + timedelta(days=(i % 45) + 1, hours=9),
                end_time=datetime.utcnow() + timedelta(days=(i % 45) + 1, hours=10),
                calendar_event_id=f"demo-calendar-event-{i + 1}",
                service=["Dental cleaning", "Teeth whitening", "Dental examination", "Root canal consultation"][i % 4],
                status="scheduled" if i % 5 else "completed",
            )
            db.add(appointment)

            db.add(ToolCallAudit(
                conversation_id=conversation.id,
                tool_name=["check_availability", "book_appointment", "reschedule_appointment"][i % 3],
                arguments={"demo": True, "record": i + 1},
                result={"success": True, "demo": True}, success=1,
            ))

        categories = ["services", "pricing", "policies", "faqs"]
        for i in range(100):
            db.add(KnowledgeBaseEntry(
                business_id=business.id, category=categories[i % 4],
                question=f"Demo question {i + 1}",
                answer=f"Adeel Dental Clinic demo information for item {i + 1}.",
            ))
            db.add(FollowUpRule(
                business_id=business.id, trigger_condition=f"inactive_{i + 1}_hours",
                delay_hours=(i % 72) + 1,
                message_template=f"Hi {{name}}, just checking in about your dental enquiry #{i + 1}.",
                active=1 if i % 5 else 0,
            ))

        db.commit()
        print(f"Seeded business: {BUSINESS_NAME} (id={business.id})")
        print("Test credentials:")
        print(f"  Email: {ADMIN_EMAIL}")
        print(f"  Password: {ADMIN_PASSWORD}")
        print("Created/reused: 100 users, leads, conversations, messages, appointments, tool audits, knowledge entries, and follow-up rules.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
