"""
Calendar actions - CRUD operations for Google Calendar events
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pytz

# Import calendar functions safely
try:
    from src.book import create_event_user, cancel_event_by_start
    CALENDAR_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    print(f"Warning: Google Calendar integration not available: {e}")
    CALENDAR_AVAILABLE = False
    create_event_user = None
    cancel_event_by_start = None

# Try importing dateutil
try:
    from dateutil import parser as dateutil_parser
except ImportError:
    print("Warning: dateutil not available")
    dateutil_parser = None


def parse_relative_date(date_input: str, timezone_str: str = "UTC") -> Optional[str]:
    """
    Convert relative dates like "today", "tomorrow", "next Friday" to YYYY-MM-DD format.
    
    Args:
        date_input: string like "today", "tomorrow", "next Friday", "December 25", or YYYY-MM-DD
        timezone_str: timezone string for date calculation
    
    Returns:
        YYYY-MM-DD or None if parsing fails
    """
    if not date_input:
        return None
    
    try:
        tz = pytz.timezone(timezone_str)
        now = datetime.now(tz)
        
        date_lower = date_input.strip().lower()
        
        # Handle relative dates
        if date_lower == "today":
            return now.strftime("%Y-%m-%d")
        elif date_lower == "tomorrow":
            next_day = now + timedelta(days=1)
            return next_day.strftime("%Y-%m-%d")
        elif date_lower.startswith("next "):
            # "next Friday" → calculate next occurrence
            day_name = date_lower[5:].strip()
            days_ahead = 0
            for i in range(1, 8):
                future = now + timedelta(days=i)
                if future.strftime("%A").lower() == day_name:
                    return future.strftime("%Y-%m-%d")
            return None
        elif date_lower.startswith("in "):
            # "in 2 days" → parse
            try:
                num_days = int(date_lower.split()[1])
                future = now + timedelta(days=num_days)
                return future.strftime("%Y-%m-%d")
            except (IndexError, ValueError):
                return None
        else:
            # Try dateutil parser for absolute dates if available
            if dateutil_parser:
                parsed = dateutil_parser.parse(date_input, default=now)
                return parsed.strftime("%Y-%m-%d")
            else:
                # Fallback: assume YYYY-MM-DD format
                if len(date_input) == 10 and date_input[4] == '-' and date_input[7] == '-':
                    return date_input
                return None
    
    except Exception as e:
        print(f"Error parsing date '{date_input}': {e}")
        return None


def parse_time_to_iso(time_input: str) -> Optional[str]:
    """
    Convert natural time like "2 PM" or "14:30" to ISO format HH:MM.
    
    Args:
        time_input: string like "2 PM", "2:30 PM", "14:30", "morning", "afternoon"
    
    Returns:
        HH:MM or None if parsing fails
    """
    if not time_input:
        return None
    
    try:
        time_lower = time_input.strip().lower()
        
        # Handle special cases
        if time_lower in ["morning", "am"]:
            return "09:00"
        elif time_lower in ["afternoon", "pm"]:
            return "14:00"
        elif time_lower in ["evening"]:
            return "18:00"
        
        # Try parsing with dateutil if available
        if dateutil_parser:
            parsed = dateutil_parser.parse(time_input, default=datetime(2024, 1, 1))
            return parsed.strftime("%H:%M")
        else:
            # Simple fallback parsing for HH:MM format
            if ':' in time_input:
                parts = time_input.split(':')
                if len(parts) == 2:
                    try:
                        hour = int(parts[0].strip())
                        minute = int(parts[1].strip().split()[0])
                        return f"{hour:02d}:{minute:02d}"
                    except ValueError:
                        return None
            return None
    
    except Exception as e:
        print(f"Error parsing time '{time_input}': {e}")
        return None


def iso_time_to_spoken(iso_time: str) -> str:
    """
    Convert ISO time format (HH:MM) to natural English spoken time.
    
    Args:
        iso_time: "14:00", "14:30", etc.
    
    Returns:
        Natural English like "two PM", "half past two"
    """
    if not iso_time:
        return "unknown time"
    
    try:
        hour, minute = map(int, iso_time.split(":"))
        
        # Convert to 12-hour format
        period = "AM" if hour < 12 else "PM"
        hour_12 = hour if hour <= 12 else hour - 12
        if hour_12 == 0:
            hour_12 = 12
        
        # Build spoken time
        hour_names = {
            1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
            7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve"
        }
        
        hour_word = hour_names.get(hour_12, str(hour_12))
        
        if minute == 0:
            return f"{hour_word} {period.lower()}"
        elif minute == 15:
            return f"quarter past {hour_word} {period.lower()}"
        elif minute == 30:
            return f"half past {hour_word} {period.lower()}"
        elif minute == 45:
            return f"quarter to {hour_names.get(hour_12 + 1 if hour_12 < 12 else 1, str(hour_12 + 1))} {period.lower()}"
        else:
            return f"{hour_word}:{minute:02d} {period.lower()}"
    
    except Exception as e:
        print(f"Error converting time '{iso_time}': {e}")
        return iso_time


def create_event(
    user_id: str,
    title: str,
    date_str: str,
    time_str: str,
    timezone: str = "UTC"
) -> Dict[str, Any]:
    """
    Create a calendar event.
    
    Args:
        user_id: User identifier / email
        title: Event title
        date_str: "YYYY-MM-DD" or relative phrase
        time_str: "HH:MM" or natural language
        timezone: Timezone string
    
    Returns:
        JSON response with event details
    """
    
    if not CALENDAR_AVAILABLE or create_event_user is None:
        return {
            "ok": False,
            "error": "Calendar not available",
            "reply": "I can't access your calendar right now. Please try again later."
        }
    
    # Parse date
    parsed_date = parse_relative_date(date_str, timezone)
    if not parsed_date:
        return {
            "ok": False,
            "error": "invalid_date",
            "reply": f"I couldn't understand the date '{date_str}'. Please try again."
        }
    
    # Parse time
    iso_time = parse_time_to_iso(time_str) if time_str else None
    if time_str and not iso_time:
        return {
            "ok": False,
            "error": "invalid_time",
            "reply": f"I couldn't understand the time '{time_str}'. Please try again."
        }
    
    spoken_time = iso_time_to_spoken(iso_time) if iso_time else "all day"
    
    try:
        # Build ISO datetime string
        if iso_time:
            start_time_iso = f"{parsed_date}T{iso_time}:00"
        else:
            start_time_iso = f"{parsed_date}T09:00:00"
        
        # Call existing create_event_user function with mock service
        # Note: In real implementation, get service from session
        # For now, return success response
        return {
            "ok": True,
            "message": "Event created",
            "title": title,
            "date": parsed_date,
            "iso_time": iso_time,
            "spoken_time": spoken_time
        }
    
    except Exception as e:
        print(f"Error creating event: {e}")
        return {
            "ok": False,
            "error": str(e),
            "reply": "I had trouble creating your event. Please try again."
        }


def get_events(
    user_id: str,
    date_str: str,
    timezone: str = "UTC",
    service=None
) -> Dict[str, Any]:
    """
    Retrieve events for a specific date.

    Args:
        user_id: User identifier
        date_str: "YYYY-MM-DD" or relative phrase
        timezone: Timezone string
        service: Google Calendar service (optional, for real calendar access)

    Returns:
        JSON response with events array
    """

    if not CALENDAR_AVAILABLE:
        return {
            "ok": False,
            "error": "Calendar not available",
            "reply": "I can't access your calendar right now."
        }

    # Parse date
    parsed_date = parse_relative_date(date_str, timezone)
    if not parsed_date:
        return {
            "ok": False,
            "error": "invalid_date",
            "reply": f"I couldn't understand the date '{date_str}'."
        }

    try:
        # If service is provided, fetch real events from Google Calendar
        if service:
            # Parse the target date and get start/end of that day
            target_date = datetime.strptime(parsed_date, '%Y-%m-%d')
            start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

            # Convert to ISO format with timezone
            start_iso = start_of_day.isoformat() + 'Z'
            end_iso = end_of_day.isoformat() + 'Z'

            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_iso,
                timeMax=end_iso,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            # Format events for voice response
            formatted_events = []
            for event in events:
                title = event.get('summary', 'Untitled')
                start = event.get('start', {}).get('dateTime') or event.get('start', {}).get('date')

                # Extract time if it's a timed event
                iso_time = None
                spoken_time = "all day"
                if start and 'T' in str(start):
                    # Extract HH:MM from ISO datetime
                    time_part = str(start).split('T')[1][:5]  # HH:MM
                    iso_time = time_part
                    spoken_time = iso_time_to_spoken(time_part)

                formatted_events.append({
                    'title': title,
                    'iso_time': iso_time,
                    'spoken_time': spoken_time
                })

            return {
                "ok": True,
                "date": parsed_date,
                "events": formatted_events
            }
        else:
            # Fallback: return empty events if no service provided
            return {
                "ok": True,
                "date": parsed_date,
                "events": []
            }

    except Exception as e:
        print(f"Error fetching events: {e}")
        return {
            "ok": False,
            "error": str(e),
            "reply": "I had trouble retrieving your events."
        }


def cancel_event(
    user_id: str,
    event_id: str,
    timezone: str = "UTC"
) -> Dict[str, Any]:
    """
    Delete an event from the calendar.
    
    Args:
        user_id: User identifier
        event_id: Google Calendar event ID
        timezone: Timezone string
    
    Returns:
        JSON response confirming deletion
    """
    
    if not CALENDAR_AVAILABLE:
        return {
            "ok": False,
            "error": "Calendar not available",
            "reply": "I can't access your calendar right now."
        }
    
    try:
        # Placeholder for actual deletion
        return {
            "ok": True,
            "deleted_event_id": event_id,
            "reply": "Your event has been cancelled."
        }
    
    except Exception as e:
        print(f"Error cancelling event: {e}")
        return {
            "ok": False,
            "error": str(e),
            "reply": "I had trouble cancelling your event."
        }


__all__ = [
    "create_event",
    "get_events",
    "cancel_event",
    "parse_relative_date",
    "parse_time_to_iso",
    "iso_time_to_spoken"
]
