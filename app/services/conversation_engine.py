import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import Conversation, Business, ConversationStatus, Appointment, LeadStatus
from app.services import conversation_service, whatsapp_service, agent_service, calendar_service
from app.llm.client import chat
import logging
import asyncio

logger = logging.getLogger(__name__)

async def process_message_with_agent(
    conversation: Conversation,
    business: Business,
    user_message: str,
    db: Session
) -> str:
    """Process user message with AI agent and return response"""

    # Build system prompt with business context
    system_prompt = agent_service.build_system_prompt(business, db)

    # Get conversation history
    history = agent_service.build_conversation_messages(conversation, db)

    # Build messages for LLM
    messages = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": user_message}
    ]

    # Get available tools
    tools = agent_service.get_available_tools()

    # Call LLM with tools
    try:
        response = await asyncio.to_thread(chat, messages, tools=tools, tool_choice="auto")
        response_message = response.choices[0].message

        # Handle tool calls if present
        if response_message.tool_calls:
            tool_results = []

            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                logger.info(f"Tool called: {function_name} with args: {arguments}")

                # Execute tool
                result = execute_tool(function_name, arguments, conversation, business, db)
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(result)
                })

            # Add assistant message and tool results to messages
            messages.append({
                "role": "assistant",
                "content": response_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in response_message.tool_calls
                ]
            })

            for tool_result in tool_results:
                messages.append(tool_result)

            # Get final response with tool results
            final_response = await asyncio.to_thread(chat, messages)
            final_message = final_response.choices[0].message.content

            return final_message

        else:
            # No tool calls, return direct response
            return response_message.content

    except Exception as e:
        logger.error(f"Error in agent processing: {e}", exc_info=True)
        return "I apologize, I'm having trouble processing your message right now. Please try again or contact us directly."

def execute_tool(
    function_name: str,
    arguments: dict,
    conversation: Conversation,
    business: Business,
    db: Session
) -> dict:
    """Execute a tool function and return result"""

    if function_name == "check_availability":
        return handle_check_availability(arguments, business, db)

    elif function_name == "book_appointment":
        return handle_book_appointment(arguments, conversation, business, db)

    elif function_name == "reschedule_appointment":
        return handle_reschedule_appointment(arguments, conversation, business, db)

    elif function_name == "cancel_appointment":
        return handle_cancel_appointment(arguments, conversation, business, db)

    elif function_name == "escalate_to_human":
        return handle_escalate_to_human(arguments, conversation, db)

    else:
        return {"error": f"Unknown tool: {function_name}"}

def handle_check_availability(arguments: dict, business: Business, db: Session) -> dict:
    """Check appointment availability using Google Calendar"""
    date_str = arguments.get("date")
    service = arguments.get("service", "general")

    # Check if calendar is connected
    credentials = business.settings.get("google_calendar_credentials") if business.settings else None

    if not credentials:
        # Fallback to mock availability if calendar not connected
        logger.warning(f"Calendar not connected for business {business.id}, using mock availability")
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            weekday = date_obj.weekday()

            if weekday == 6:  # Sunday
                return {
                    "available": False,
                    "reason": "We are closed on Sundays"
                }

            # Generate mock time slots
            if weekday < 5:  # Mon-Fri
                slots = ["9:00 AM", "10:30 AM", "2:00 PM", "4:00 PM"]
            else:  # Saturday
                slots = ["9:00 AM", "11:00 AM"]

            return {
                "available": True,
                "date": date_str,
                "service": service,
                "available_slots": slots,
                "message": f"We have availability on {date_str} at the following times: {', '.join(slots)}"
            }
        except ValueError:
            return {"error": "Invalid date format. Please use YYYY-MM-DD"}

    # Use real Google Calendar
    try:
        result = calendar_service.check_availability(
            credentials_json=credentials,
            date=date_str,
            service=service,
            duration_minutes=60
        )
        return result
    except Exception as e:
        logger.error(f"Error checking calendar availability: {e}", exc_info=True)
        return {"error": f"Failed to check availability: {str(e)}"}

def handle_book_appointment(
    arguments: dict,
    conversation: Conversation,
    business: Business,
    db: Session
) -> dict:
    """Book an appointment with Google Calendar integration"""
    date_str = arguments.get("date")
    time_str = arguments.get("time")
    service = arguments.get("service")
    patient_name = arguments.get("patient_name")

    try:
        # Parse datetime
        datetime_str = f"{date_str} {time_str}"
        start_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        end_time = start_time + timedelta(minutes=60)  # Default 60 min duration

        # Create appointment in database
        appointment = Appointment(
            business_id=business.id,
            lead_id=conversation.lead_id,
            start_time=start_time,
            end_time=end_time,
            service=service,
            status="scheduled"
        )
        db.add(appointment)

        # Update lead name if provided
        lead = conversation.lead
        if patient_name and not lead.name:
            lead.name = patient_name

        # Check if calendar is connected
        credentials = business.settings.get("google_calendar_credentials") if business.settings else None

        if credentials:
            # Create event in Google Calendar
            calendar_result = calendar_service.create_calendar_event(
                credentials_json=credentials,
                summary=f"{service} - {patient_name}",
                start_time=start_time,
                end_time=end_time,
                description=f"Service: {service}\nPatient: {patient_name}\nPhone: {lead.phone}",
                attendee_email=lead.email if lead.email else None
            )

            if calendar_result.get("success"):
                appointment.calendar_event_id = calendar_result["event_id"]
                logger.info(f"Calendar event created: {calendar_result['event_id']}")
            else:
                logger.warning(f"Failed to create calendar event: {calendar_result.get('error')}")
        else:
            logger.info(f"Calendar not connected for business {business.id}, appointment saved without calendar event")

        db.commit()
        db.refresh(appointment)
        conversation.lead.status = LeadStatus.BOOKED
        db.commit()

        logger.info(f"Appointment booked: {appointment.id} for {patient_name}")

        return {
            "success": True,
            "appointment_id": appointment.id,
            "date": date_str,
            "time": time_str,
            "service": service,
            "patient_name": patient_name,
            "message": f"Appointment confirmed for {patient_name} on {date_str} at {time_str} for {service}"
        }

    except ValueError as e:
        return {"error": f"Invalid date/time format: {str(e)}"}
    except Exception as e:
        logger.error(f"Error booking appointment: {e}", exc_info=True)
        db.rollback()
        return {"error": "Failed to book appointment. Please try again."}


def handle_reschedule_appointment(arguments, conversation, business, db) -> dict:
    appointment = db.query(Appointment).filter(
        Appointment.id == arguments.get("appointment_id"),
        Appointment.business_id == business.id,
        Appointment.lead_id == conversation.lead_id,
        Appointment.status == "scheduled"
    ).first()
    if not appointment:
        return {"error": "Appointment not found"}
    try:
        start = datetime.strptime(f"{arguments['new_date']} {arguments['new_time']}", "%Y-%m-%d %H:%M")
    except (KeyError, ValueError):
        return {"error": "Invalid date/time format"}
    end = start + timedelta(minutes=60)
    credentials = business.settings.get("google_calendar_credentials") if business.settings else None
    if credentials and appointment.calendar_event_id:
        result = calendar_service.update_calendar_event(credentials, appointment.calendar_event_id, start, end)
        if not result.get("success"):
            return {"error": "Unable to update calendar appointment"}
    appointment.start_time, appointment.end_time = start, end
    db.commit()
    return {"success": True, "appointment_id": appointment.id, "date": arguments['new_date'], "time": arguments['new_time']}


def handle_cancel_appointment(arguments, conversation, business, db) -> dict:
    appointment = db.query(Appointment).filter(
        Appointment.id == arguments.get("appointment_id"),
        Appointment.business_id == business.id,
        Appointment.lead_id == conversation.lead_id,
        Appointment.status == "scheduled"
    ).first()
    if not appointment:
        return {"error": "Appointment not found"}
    credentials = business.settings.get("google_calendar_credentials") if business.settings else None
    if credentials and appointment.calendar_event_id:
        result = calendar_service.delete_calendar_event(credentials, appointment.calendar_event_id)
        if not result.get("success"):
            return {"error": "Unable to cancel calendar appointment"}
    appointment.status = "cancelled"
    db.commit()
    return {"success": True, "appointment_id": appointment.id, "message": "Appointment cancelled"}

def handle_escalate_to_human(arguments: dict, conversation: Conversation, db: Session) -> dict:
    """Escalate conversation to human staff"""
    reason = arguments.get("reason", "User requested human assistance")

    # Update conversation status
    conversation.status = ConversationStatus.HUMAN_TAKEOVER
    db.commit()

    logger.info(f"Conversation {conversation.id} escalated to human: {reason}")

    return {
        "success": True,
        "message": "Conversation has been escalated to a staff member. They will respond shortly.",
        "reason": reason
    }
