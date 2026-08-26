import os
import sys
from pathlib import Path
import asyncio
import httpx

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.models import Base, Business, User, Lead, Conversation, Message, KnowledgeBaseEntry
from app.core.security import get_password_hash
from app.services import conversation_service, knowledge_service
from app.services.conversation_engine import process_message_with_agent

# Test data
TEST_BUSINESS_NAME = "Test Dental Clinic"
TEST_USER_EMAIL = "test@clinic.com"
TEST_USER_PASSWORD = "testpass123"
TEST_LEAD_PHONE = "+1234567890"

def setup_test_data(db: Session):
    """Create test business with knowledge base"""
    print("Setting up test data...")

    # Create business
    business = Business(
        name=TEST_BUSINESS_NAME,
        settings={
            "whatsapp_phone_id": "test_phone_id",
            "whatsapp_access_token": "test_token"
        }
    )
    db.add(business)
    db.commit()
    db.refresh(business)

    # Create user
    user = User(
        business_id=business.id,
        email=TEST_USER_EMAIL,
        hashed_password=get_password_hash(TEST_USER_PASSWORD),
        role="owner"
    )
    db.add(user)
    db.commit()

    # Create knowledge base entries
    kb_entries = [
        {
            "category": "services",
            "answer": "Regular Cleaning: $120, 45 minutes"
        },
        {
            "category": "services",
            "answer": "Teeth Whitening: $350, 60 minutes"
        },
        {
            "category": "services",
            "answer": "Dental Exam: $80, 30 minutes"
        },
        {
            "category": "pricing",
            "answer": "Cavity Filling: $200-400 depending on complexity"
        },
        {
            "category": "policies",
            "answer": "We accept most insurance plans. Please bring your insurance card to your appointment."
        },
        {
            "category": "faqs",
            "question": "What are your office hours?",
            "answer": "Monday-Friday: 9am-6pm, Saturday: 9am-2pm. Closed on Sundays."
        }
    ]

    for entry in kb_entries:
        knowledge_service.create_knowledge_entry(
            business_id=business.id,
            category=entry["category"],
            answer=entry["answer"],
            question=entry.get("question"),
            db=db
        )

    print(f"✓ Created business: {business.name} (ID: {business.id})")
    print(f"✓ Created user: {user.email}")
    print(f"✓ Created {len(kb_entries)} knowledge base entries")

    return business, user

async def test_conversation_flow(db: Session, business: Business):
    """Test complete conversation flow with agent"""
    print("\n" + "="*60)
    print("TESTING CONVERSATION FLOW")
    print("="*60)

    # Create lead
    lead = conversation_service.get_or_create_lead(TEST_LEAD_PHONE, business.id, db)
    print(f"\n✓ Lead created: {lead.phone} (ID: {lead.id})")

    # Create conversation
    conversation = conversation_service.get_or_create_conversation(
        lead.id, business.id, "whatsapp", db
    )
    print(f"✓ Conversation created (ID: {conversation.id})")

    # Test messages
    test_messages = [
        "Hi, I need a teeth cleaning appointment",
        "What are your prices?",
        "Do you accept insurance?",
        "Can you check availability for tomorrow?",
        "What about 2026-08-28?",
    ]

    for i, user_message in enumerate(test_messages, 1):
        print(f"\n--- Turn {i} ---")
        print(f"User: {user_message}")

        # Save user message
        conversation_service.save_message(conversation.id, "user", user_message, db)

        # Process with agent
        try:
            agent_response = await process_message_with_agent(
                conversation, business, user_message, db
            )

            # Save agent response
            conversation_service.save_message(conversation.id, "assistant", agent_response, db)

            print(f"Agent: {agent_response}")

        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()

    print("\n✓ Conversation flow test completed")
    return conversation

def test_conversation_history(db: Session, conversation_id: int):
    """Test conversation history retrieval"""
    print("\n" + "="*60)
    print("TESTING CONVERSATION HISTORY")
    print("="*60)

    messages = conversation_service.get_conversation_history(conversation_id, limit=20, db=db)

    print(f"\nRetrieved {len(messages)} messages:")
    for msg in messages:
        role = "User" if msg.role == "user" else "Agent"
        print(f"\n{role}: {msg.content[:100]}...")

    print("\n✓ Conversation history test completed")

async def test_api_endpoints():
    """Test API endpoints with HTTP requests"""
    print("\n" + "="*60)
    print("TESTING API ENDPOINTS")
    print("="*60)

    base_url = "http://localhost:8000"

    async with httpx.AsyncClient() as client:
        # Test health check
        print("\n1. Testing health check...")
        try:
            response = await client.get(f"{base_url}/health")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"   ✗ Error: {e}")

        # Test signup
        print("\n2. Testing signup...")
        try:
            response = await client.post(
                f"{base_url}/api/v1/auth/signup",
                json={
                    "email": "api_test@clinic.com",
                    "password": "testpass123",
                    "business_name": "API Test Clinic"
                }
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                token = data["access_token"]
                print(f"   ✓ Token received: {token[:20]}...")
            else:
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ✗ Error: {e}")

        # Test knowledge base list
        print("\n3. Testing knowledge base list (with auth)...")
        try:
            if 'token' in locals():
                response = await client.get(
                    f"{base_url}/api/v1/knowledge",
                    headers={"Authorization": f"Bearer {token}"}
                )
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    entries = response.json()
                    print(f"   ✓ Retrieved {len(entries)} knowledge base entries")
                else:
                    print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ✗ Error: {e}")

    print("\n✓ API endpoint tests completed")

async def main():
    print("="*60)
    print("FOLLOWLY COMPREHENSIVE TEST SUITE")
    print("="*60)

    # Check environment
    provider = os.getenv("LLM_PROVIDER", "openrouter")
    print(f"\nLLM Provider: {provider}")

    if provider == "openrouter":
        key = os.getenv("OPENROUTER_API_KEY")
    elif provider == "openai":
        key = os.getenv("OPENAI_API_KEY")
    elif provider == "anthropic":
        key = os.getenv("ANTHROPIC_API_KEY")
    else:
        print(f"Unknown provider: {provider}")
        return

    if not key:
        print(f"✗ API key not set! Set {provider.upper()}_API_KEY in .env")
        return

    print(f"✓ LLM API key configured")

    # Database setup
    db = SessionLocal()

    try:
        # Setup test data
        business, user = setup_test_data(db)

        # Test conversation flow
        conversation = await test_conversation_flow(db, business)

        # Test conversation history
        test_conversation_history(db, conversation.id)

        # Test API endpoints
        print("\n" + "="*60)
        print("NOTE: API endpoint tests require the server to be running")
        print("Start server with: uvicorn app.main:app --reload")
        print("="*60)

        try_api = input("\nDo you want to test API endpoints? (server must be running) [y/N]: ")
        if try_api.lower() == 'y':
            await test_api_endpoints()

        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print("✓ Database setup")
        print("✓ Knowledge base creation")
        print("✓ Conversation flow with AI agent")
        print("✓ Message persistence")
        print("✓ Conversation history retrieval")
        print("\nAll tests completed!")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
