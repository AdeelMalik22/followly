from sqlalchemy.orm import Session
from typing import List, Dict
from app.models.models import Business, Conversation, Message
from app.services.knowledge_service import get_knowledge_entries

def build_system_prompt(business: Business, db: Session) -> str:
    """Build system prompt with business context and knowledge base"""

    # Get all knowledge base entries
    knowledge_entries = get_knowledge_entries(business.id, db=db)

    # Organize by category
    kb_by_category = {}
    for entry in knowledge_entries:
        if entry.category not in kb_by_category:
            kb_by_category[entry.category] = []
        kb_by_category[entry.category].append(entry)

    # Build knowledge base sections
    kb_sections = []

    if "services" in kb_by_category:
        services_text = "\n".join([f"- {e.answer}" for e in kb_by_category["services"]])
        kb_sections.append(f"**Services Offered:**\n{services_text}")

    if "pricing" in kb_by_category:
        pricing_text = "\n".join([f"- {e.answer}" for e in kb_by_category["pricing"]])
        kb_sections.append(f"**Pricing:**\n{pricing_text}")

    if "policies" in kb_by_category:
        policies_text = "\n".join([f"- {e.answer}" for e in kb_by_category["policies"]])
        kb_sections.append(f"**Policies:**\n{policies_text}")

    if "faqs" in kb_by_category:
        faqs_text = "\n".join([f"Q: {e.question}\nA: {e.answer}" for e in kb_by_category["faqs"] if e.question])
        kb_sections.append(f"**Common Questions:**\n{faqs_text}")

    kb_text = "\n\n".join(kb_sections) if kb_sections else "No knowledge base entries yet."

    # Build system prompt
    system_prompt = f"""You are an AI assistant for {business.name}, a dental clinic.

Your role:
- Answer questions about services and pricing
- Qualify potential patients by understanding their needs
- Be friendly, professional, and concise
- If asked about appointment booking, explain you can help check availability (use the check_availability tool)
- If you don't know something, say so - never make up information

{kb_text}

Current date: 2026-08-26

Keep responses brief and conversational. Always prioritize information from the knowledge base above."""

    return system_prompt

def build_conversation_messages(conversation: Conversation, db: Session) -> List[Dict[str, str]]:
    """Build message history for LLM context"""
    from app.services.conversation_service import get_conversation_history

    messages = get_conversation_history(conversation.id, limit=20, db=db)

    return [
        {
            "role": "user" if msg.role == "user" else "assistant",
            "content": msg.content
        }
        for msg in messages
    ]

def get_available_tools() -> List[Dict]:
    """Define tools available to the agent"""
    return [
        {
            "type": "function",
            "function": {
                "name": "check_availability",
                "description": "Check available appointment slots for a specific date and service",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format"
                        },
                        "service": {
                            "type": "string",
                            "description": "Type of service (e.g., cleaning, whitening, exam)"
                        }
                    },
                    "required": ["date"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "book_appointment",
                "description": "Book an appointment for the patient",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format"
                        },
                        "time": {
                            "type": "string",
                            "description": "Time in HH:MM format (24-hour)"
                        },
                        "service": {
                            "type": "string",
                            "description": "Type of service"
                        },
                        "patient_name": {
                            "type": "string",
                            "description": "Patient's full name"
                        }
                    },
                    "required": ["date", "time", "service", "patient_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "escalate_to_human",
                "description": "Transfer conversation to a human staff member when needed",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Brief reason for escalation"
                        }
                    },
                    "required": ["reason"]
                }
            }
        }
    ]
