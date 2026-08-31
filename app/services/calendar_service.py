from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service(credentials_json: dict):
    """Create Google Calendar service from credentials"""
    creds = Credentials.from_authorized_user_info(credentials_json, SCOPES)

    # Refresh token if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    service = build('calendar', 'v3', credentials=creds)
    return service, creds

def create_oauth_flow(client_id: str, client_secret: str, redirect_uri: str) -> Flow:
    """Create OAuth flow for calendar authorization"""
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        },
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    return flow

def check_availability(
    credentials_json: dict,
    date: str,
    service: Optional[str] = None,
    duration_minutes: int = 60,
    working_hours: Optional[dict] = None,
) -> Dict:
    """Check available time slots for a specific date"""
    try:
        service_obj, _ = get_calendar_service(credentials_json)

        # Parse date
        target_date = datetime.strptime(date, "%Y-%m-%d")

        day_name = target_date.strftime("%A").lower()
        day_hours = (working_hours or {}).get(day_name)
        if day_hours is None:
            day_hours = {"open": day_name != "sunday", "start": "09:00", "end": "17:00"}
        if not day_hours.get("open", False):
            return {
                "available": False,
                "reason": f"We are closed on {day_name.title()}",
                "date": date
            }

        try:
            start_time = datetime.strptime(day_hours.get("start", "09:00"), "%H:%M").time()
            end_time = datetime.strptime(day_hours.get("end", "17:00"), "%H:%M").time()
        except (TypeError, ValueError):
            return {"available": False, "reason": "Business working hours are invalid", "date": date}
        if start_time >= end_time:
            return {"available": False, "reason": "Business working hours are invalid", "date": date}

        # Set time range for freebusy query
        time_min = target_date.replace(hour=start_time.hour, minute=start_time.minute, second=0)
        time_max = target_date.replace(hour=end_time.hour, minute=end_time.minute, second=0)

        # Query free/busy
        body = {
            "timeMin": time_min.isoformat() + 'Z',
            "timeMax": time_max.isoformat() + 'Z',
            "items": [{"id": "primary"}]
        }

        freebusy = service_obj.freebusy().query(body=body).execute()
        busy_periods = freebusy['calendars']['primary'].get('busy', [])

        # Generate time slots
        available_slots = []
        current_time = time_min
        slot_duration = timedelta(minutes=duration_minutes)

        while current_time + slot_duration <= time_max:
            slot_end = current_time + slot_duration

            # Check if slot overlaps with busy period
            is_available = True
            for busy in busy_periods:
                busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
                busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))

                # Remove timezone info for comparison
                busy_start = busy_start.replace(tzinfo=None)
                busy_end = busy_end.replace(tzinfo=None)

                if (current_time < busy_end and slot_end > busy_start):
                    is_available = False
                    break

            if is_available:
                available_slots.append(current_time.strftime("%I:%M %p"))

            # Move to next slot (30 min intervals)
            current_time += timedelta(minutes=30)

        if not available_slots:
            return {
                "available": False,
                "reason": "No available slots on this date",
                "date": date
            }

        return {
            "available": True,
            "date": date,
            "service": service,
            "available_slots": available_slots[:6],  # Return max 6 slots
            "message": f"Available times on {date}: {', '.join(available_slots[:6])}"
        }

    except Exception as e:
        logger.error(f"Error checking availability: {e}", exc_info=True)
        return {
            "error": f"Failed to check availability: {str(e)}"
        }

def create_calendar_event(
    credentials_json: dict,
    summary: str,
    start_time: datetime,
    end_time: datetime,
    description: Optional[str] = None,
    attendee_email: Optional[str] = None
) -> Dict:
    """Create a calendar event"""
    try:
        service_obj, _ = get_calendar_service(credentials_json)

        event = {
            'summary': summary,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC',
            },
        }

        if description:
            event['description'] = description

        if attendee_email:
            event['attendees'] = [{'email': attendee_email}]

        created_event = service_obj.events().insert(
            calendarId='primary',
            body=event,
            sendUpdates='all' if attendee_email else 'none'
        ).execute()

        return {
            "success": True,
            "event_id": created_event['id'],
            "event_link": created_event.get('htmlLink'),
            "message": "Calendar event created successfully"
        }

    except Exception as e:
        logger.error(f"Error creating calendar event: {e}", exc_info=True)
        return {
            "error": f"Failed to create event: {str(e)}"
        }

def update_calendar_event(
    credentials_json: dict,
    event_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    summary: Optional[str] = None
) -> Dict:
    """Update an existing calendar event"""
    try:
        service_obj, _ = get_calendar_service(credentials_json)

        # Get existing event
        event = service_obj.events().get(
            calendarId='primary',
            eventId=event_id
        ).execute()

        # Update fields
        if summary:
            event['summary'] = summary
        if start_time:
            event['start']['dateTime'] = start_time.isoformat()
        if end_time:
            event['end']['dateTime'] = end_time.isoformat()

        updated_event = service_obj.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event
        ).execute()

        return {
            "success": True,
            "event_id": updated_event['id'],
            "message": "Event updated successfully"
        }

    except Exception as e:
        logger.error(f"Error updating calendar event: {e}", exc_info=True)
        return {
            "error": f"Failed to update event: {str(e)}"
        }

def delete_calendar_event(credentials_json: dict, event_id: str) -> Dict:
    """Delete a calendar event"""
    try:
        service_obj, _ = get_calendar_service(credentials_json)

        service_obj.events().delete(
            calendarId='primary',
            eventId=event_id
        ).execute()

        return {
            "success": True,
            "message": "Event deleted successfully"
        }

    except Exception as e:
        logger.error(f"Error deleting calendar event: {e}", exc_info=True)
        return {
            "error": f"Failed to delete event: {str(e)}"
        }
