import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.core.config import settings
from sqlalchemy.orm import Session
from app.models.models import Conversation, Business, ConversationStatus, Appointment, LeadStatus, ToolCallAudit
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
        for _ in range(3):
            response = await asyncio.to_thread(chat, messages, tools=tools, tool_choice="auto")
            response_message = response.choices[0].message
            if not response_message.tool_calls:
                return response_message.content

            tool_results = []

            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                logger.info(f"Tool called: {function_name} with args: {arguments}")

                # Execute tool
                try:
                    result = await execute_tool(function_name, arguments, conversation, business, db)
                    audit = ToolCallAudit(
                        conversation_id=conversation.id,
                        tool_name=function_name,
                        arguments=arguments,
                        result=result,
                        success=1
                    )
                except Exception as exc:
                    result = {"error": "Tool execution failed"}
                    audit = ToolCallAudit(
                        conversation_id=conversation.id,
                        tool_name=function_name,
                        arguments=arguments,
                        result=result,
                        success=0,
                        error=str(exc)
                    )
                db.add(audit)
                db.commit()
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(result)
                })

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
        return "I’m sorry, I couldn’t complete that request. Please try again."

    except Exception as e:
        logger.error(f"Error in agent processing: {e}", exc_info=True)
        try:
            conversation.status = ConversationStatus.HUMAN_TAKEOVER
            db.commit()
            logger.warning("Conversation %s marked for human review after agent failure", conversation.id)
        except Exception:
            db.rollback()
            logger.error("Could not mark conversation %s for human review", conversation.id, exc_info=True)
        return "I apologize, I'm having trouble processing your message right now. Please try again or contact us directly."

async def execute_tool(
    function_name: str,
    arguments: dict,
    conversation: Conversation,
    business: Business,
    db: Session
) -> dict:
    """Execute a tool function and return result"""

    if function_name == "check_availability":
        return await handle_check_availability(arguments, business, db)

    elif function_name == "book_appointment":
        return await handle_book_appointment(arguments, conversation, business, db)

    elif function_name == "reschedule_appointment":
        return await handle_reschedule_appointment(arguments, conversation, business, db)

    elif function_name == "cancel_appointment":
        return await handle_cancel_appointment(arguments, conversation, business, db)

    elif function_name == "escalate_to_human":
        return handle_escalate_to_human(arguments, conversation, db)

    else:
        return {"error": f"Unknown tool: {function_name}"}

async def handle_check_availability(arguments: dict, business: Business, db: Session) -> dict:
    """Check appointment availability using Google Calendar"""
    date_str = arguments.get("date")
    service = arguments.get("service", "general")
    business_settings = business.settings or {}
    working_hours = business_settings.get("working_hours", {})
    duration_minutes = business_settings.get("appointment_duration_minutes", 60)
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    except (TypeError, ValueError):
        return {"error": "Invalid date format. Please use YYYY-MM-DD"}

    # Check if calendar is connected
    credentials = business.settings.get("google_calendar_credentials") if business.settings else None

    if not credentials:
        # Fallback to mock availability if calendar not connected
        logger.warning(f"Calendar not connected for business {business.id}, using mock availability")
        try:
            weekday = date_obj.weekday()
            day_name = date_obj.strftime("%A").lower()
            day_hours = working_hours.get(day_name)
            if day_hours and not day_hours.get("open", False):
                return {
                    "available": False,
                    "reason": f"We are closed on {day_name.title()}"
                }

            start_text = (day_hours or {}).get("start", "09:00")
            end_text = (day_hours or {}).get("end", "17:00")
            start = datetime.strptime(start_text, "%H:%M")
            end = datetime.strptime(end_text, "%H:%M")
            if start >= end:
                return {"available": False, "reason": f"{day_name.title()} has invalid working hours"}

            # Generate slots within this business's configured hours.
            slots = []
            cursor = start
            while cursor + timedelta(minutes=duration_minutes) <= end:
                slots.append(cursor.strftime("%-I:%M %p"))
                cursor += timedelta(minutes=30)

            # Do not offer slots that have already passed today.
            local_now = datetime.now(ZoneInfo(settings.BUSINESS_TIMEZONE))
            if date_obj.date() == local_now.date():
                slots = [slot for slot in slots if datetime.strptime(slot, "%I:%M %p").time() > local_now.time()]

            return {
                "available": True,
                "date": date_str,
                "service": service,
                "duration_minutes": duration_minutes,
                "available_slots": slots,
                "message": f"We have availability on {date_str} at the following times: {', '.join(slots)}"
            }
        except ValueError:
            return {"error": "Invalid date format. Please use YYYY-MM-DD"}

    # Use real Google Calendar
    try:
        result = await asyncio.to_thread(
            calendar_service.check_availability,
            credentials_json=credentials, date=date_str, service=service,
            duration_minutes=duration_minutes,
            working_hours=working_hours,
        )
        # Google returns free slots across the requested day; remove elapsed
        # slots when the requested date is today in the business timezone.
        local_now = datetime.now(ZoneInfo(settings.BUSINESS_TIMEZONE))
        if date_obj.date() == local_now.date() and result.get("available_slots"):
            result["available_slots"] = [
                slot for slot in result["available_slots"]
                if datetime.strptime(slot, "%I:%M %p").time() > local_now.time()
            ]
        return result
    except Exception as e:
        logger.error(f"Error checking calendar availability: {e}", exc_info=True)
        return {"error": f"Failed to check availability: {str(e)}"}

async def handle_book_appointment(
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
        duration_minutes = (business.settings or {}).get("appointment_duration_minutes", 60)
        if not isinstance(duration_minutes, int) or not 15 <= duration_minutes <= 480:
            return {"success": False, "error": "This business has an invalid appointment duration configured."}
        end_time = start_time + timedelta(minutes=duration_minutes)

        # A booking must fit completely inside the business's hours.
        day_name = start_time.strftime("%A").lower()
        configured_hours = (business.settings or {}).get("working_hours", {})
        day_hours = configured_hours.get(day_name)
        if day_hours is None:
            day_hours = {"open": day_name != "sunday", "start": "09:00", "end": "17:00"}
        if not day_hours.get("open", False):
            return {"success": False, "error": f"The business is closed on {day_name.title()}."}
        try:
            opening = datetime.strptime(day_hours.get("start", "09:00"), "%H:%M").time()
            closing = datetime.strptime(day_hours.get("end", "17:00"), "%H:%M").time()
        except (TypeError, ValueError):
            return {"success": False, "error": "This business has invalid working hours configured."}
        if opening >= closing or start_time.time() < opening or end_time.time() > closing:
            return {"success": False, "error": f"That appointment is outside business hours on {day_name.title()}."}

        # Prevent double booking within this business. Two appointments
        # overlap when the existing one starts before the requested one ends
        # and ends after the requested one starts.
        overlapping = db.query(Appointment.id).filter(
            Appointment.business_id == business.id,
            Appointment.status == "scheduled",
            Appointment.start_time < end_time,
            Appointment.end_time > start_time,
        ).first()
        if overlapping:
            return {
                "success": False,
                "error": "That time slot is no longer available. Please choose another available time.",
            }

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
            calendar_result = await asyncio.to_thread(
                calendar_service.create_calendar_event,
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


async def handle_reschedule_appointment(arguments, conversation, business, db) -> dict:
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
        result = await asyncio.to_thread(calendar_service.update_calendar_event, credentials, appointment.calendar_event_id, start, end)
        if not result.get("success"):
            return {"error": "Unable to update calendar appointment"}
    appointment.start_time, appointment.end_time = start, end
    db.commit()
    return {"success": True, "appointment_id": appointment.id, "date": arguments['new_date'], "time": arguments['new_time']}


async def handle_cancel_appointment(arguments, conversation, business, db) -> dict:
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
        result = await asyncio.to_thread(calendar_service.delete_calendar_event, credentials, appointment.calendar_event_id)
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
