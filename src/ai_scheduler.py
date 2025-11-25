"""
AI Smart Scheduling Module

Finds the best time slots for events based on:
- Google Calendar availability
- User preferences (e.g., no mornings, no weekends)
- Event duration requirements
- GPT-powered time recommendation
"""

import datetime
from typing import Optional, Dict, Any, List, Tuple
import os
import json
from dataclasses import dataclass, asdict

try:
    from google.auth.transport.requests import Request
    from google.oauth2.service_account import Credentials
    from google.oauth2.credentials import Credentials as OAuthCredentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request as GoogleRequest
    from googleapiclient.discovery import build
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


@dataclass
class TimeSlot:
    """Represents an available time slot."""
    start: datetime.datetime
    end: datetime.datetime
    duration_minutes: int
    reason: str = "available"  # e.g., "available", "preferred_time", "moderate_fit"

    def to_dict(self):
        return {
            'start': self.start.isoformat(),
            'end': self.end.isoformat(),
            'duration_minutes': self.duration_minutes,
            'reason': self.reason
        }


@dataclass
class SchedulePreferences:
    """User scheduling preferences."""
    avoid_times: List[str] = None  # e.g., ['morning', 'evening', 'weekend']
    preferred_times: List[str] = None  # e.g., ['afternoon', 'late_morning']
    min_gap_minutes: int = 15  # Minimum gap between events
    work_hours_only: bool = True  # 9-17 Mon-Fri
    earliest_hour: int = 9  # Earliest acceptable hour
    latest_hour: int = 17  # Latest acceptable hour

    def __post_init__(self):
        if self.avoid_times is None:
            self.avoid_times = []
        if self.preferred_times is None:
            self.preferred_times = []


class GoogleCalendarHelper:
    """Handles Google Calendar API interactions."""

    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.json'):
        """Initialize Google Calendar helper with OAuth credentials."""
        if not HAS_GOOGLE:
            raise ImportError("Google API client not installed. Install with: pip install google-auth-oauthlib google-api-python-client")
        
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Calendar API."""
        creds = None
        if os.path.exists(self.token_path):
            creds = OAuthCredentials.from_authorized_user_file(self.token_path, self.SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(GoogleRequest())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=creds)

    def get_events(
        self,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        calendar_id: str = 'primary'
    ) -> List[Dict[str, Any]]:
        """Fetch events from Google Calendar for a date range."""
        if not self.service:
            return []

        try:
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=start_date.isoformat() + 'Z',
                timeMax=end_date.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            return events_result.get('items', [])
        except Exception as e:
            print(f"Error fetching calendar events: {e}")
            return []


class AvailabilityBuilder:
    """Builds availability blocks from calendar events."""

    def __init__(self, preferences: Optional[SchedulePreferences] = None):
        self.preferences = preferences or SchedulePreferences()

    def build_availability_blocks(
        self,
        events: List[Dict[str, Any]],
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        duration_minutes: int
    ) -> List[TimeSlot]:
        """
        Build list of available time slots given busy events.
        
        Args:
            events: List of calendar events (from Google Calendar API)
            start_date: Start of search window
            end_date: End of search window
            duration_minutes: Required duration for the slot
        
        Returns:
            List of TimeSlot objects representing available times
        """
        # Parse events into busy blocks
        busy_blocks = []
        for event in events:
            start_str = event.get('start', {}).get('dateTime') or event.get('start', {}).get('date')
            end_str = event.get('end', {}).get('dateTime') or event.get('end', {}).get('date')
            
            if start_str and end_str:
                try:
                    # Handle both datetime and date formats
                    if 'T' in start_str:
                        start = datetime.datetime.fromisoformat(start_str.replace('Z', '+00:00')).astimezone()
                        end = datetime.datetime.fromisoformat(end_str.replace('Z', '+00:00')).astimezone()
                    else:
                        start = datetime.datetime.fromisoformat(start_str).replace(hour=0, minute=0)
                        end = datetime.datetime.fromisoformat(end_str).replace(hour=0, minute=0)
                    busy_blocks.append((start, end))
                except Exception:
                    continue

        # Sort busy blocks
        busy_blocks.sort(key=lambda x: x[0])

        # Find gaps
        available_slots = []
        current_time = start_date

        for busy_start, busy_end in busy_blocks:
            # Gap before this busy block
            if current_time < busy_start:
                gap_duration = (busy_start - current_time).total_seconds() / 60
                if gap_duration >= duration_minutes:
                    slot = TimeSlot(
                        start=current_time,
                        end=busy_start,
                        duration_minutes=int(gap_duration)
                    )
                    if self._passes_preferences(current_time):
                        available_slots.append(slot)
            
            current_time = max(current_time, busy_end)

        # Gap after last event
        if current_time < end_date:
            gap_duration = (end_date - current_time).total_seconds() / 60
            if gap_duration >= duration_minutes:
                slot = TimeSlot(
                    start=current_time,
                    end=end_date,
                    duration_minutes=int(gap_duration)
                )
                if self._passes_preferences(current_time):
                    available_slots.append(slot)

        return available_slots

    def _passes_preferences(self, slot_time: datetime.datetime) -> bool:
        """Check if a time slot passes preference filters."""
        hour = slot_time.hour
        weekday = slot_time.weekday()  # 0=Monday, 6=Sunday

        # Check work hours
        if self.preferences.work_hours_only:
            if hour < self.preferences.earliest_hour or hour >= self.preferences.latest_hour:
                return False
            if weekday >= 5:  # Skip weekends
                return False

        # Check avoided times
        if 'morning' in self.preferences.avoid_times and hour < 12:
            return False
        if 'evening' in self.preferences.avoid_times and hour >= 17:
            return False
        if 'weekend' in self.preferences.avoid_times and weekday >= 5:
            return False

        return True


class GPTTimeRecommender:
    """Uses GPT to recommend the best time slots."""

    def __init__(self, api_key: Optional[str] = None):
        if not HAS_OPENAI:
            raise ImportError("OpenAI not installed. Install with: pip install openai")
        
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key

    def recommend_best_times(
        self,
        slots: List[TimeSlot],
        event_description: str,
        preferences_description: str,
        top_n: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Use GPT to evaluate and rank available time slots.
        
        Args:
            slots: List of available TimeSlot objects
            event_description: Description of the event (e.g., "2-hour team meeting")
            preferences_description: User preferences summary
            top_n: Number of top recommendations to return
        
        Returns:
            List of recommended time slots with reasoning
        """
        if not slots:
            return []

        # Format slots for GPT
        slots_text = "\n".join([
            f"- {slot.start.strftime('%A, %B %d at %I:%M %p')} to {slot.end.strftime('%I:%M %p')} "
            f"({slot.duration_minutes} min available)"
            for slot in slots[:10]  # Limit to top 10 to avoid token overflow
        ])

        prompt = f"""You are a smart scheduling assistant. Given available time slots and event requirements, 
recommend the top {top_n} best times.

Event: {event_description}
User Preferences: {preferences_description}

Available slots:
{slots_text}

For each recommendation, explain why it's a good choice. Consider:
1. Time of day suitability
2. Sufficient duration
3. Buffer time from other events
4. Alignment with preferences

Respond in JSON format:
[
  {{"start": "ISO datetime", "reason": "why this is good"}},
  ...
]"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            content = response['choices'][0]['message']['content']
            # Extract JSON from response
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                recommendations = json.loads(json_match.group())
                return recommendations[:top_n]
        except Exception as e:
            print(f"Error calling GPT: {e}")

        # Fallback: return first N slots with basic reasoning
        return [
            {
                'start': slot.start.isoformat(),
                'end': slot.end.isoformat(),
                'reason': f"Available slot at {slot.start.strftime('%A %I:%M %p')}"
            }
            for slot in slots[:top_n]
        ]


class SmartScheduler:
    """Main orchestrator for AI-powered scheduling."""

    def __init__(
        self,
        google_credentials_path: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        preferences: Optional[SchedulePreferences] = None
    ):
        self.preferences = preferences or SchedulePreferences()
        self.google_helper = None
        self.recommender = None

        if google_credentials_path:
            try:
                self.google_helper = GoogleCalendarHelper(google_credentials_path)
            except Exception as e:
                print(f"Warning: Could not initialize Google Calendar: {e}")

        if openai_api_key or os.getenv('OPENAI_API_KEY'):
            try:
                self.recommender = GPTTimeRecommender(openai_api_key)
            except Exception as e:
                print(f"Warning: Could not initialize GPT recommender: {e}")

    def find_best_times(
        self,
        event_description: str,
        duration_minutes: int,
        search_window_days: int = 7,
        top_n: int = 3,
        start_date: Optional[datetime.datetime] = None
    ) -> Dict[str, Any]:
        """
        Find the best times for an event.
        
        Args:
            event_description: Description of the event
            duration_minutes: Required duration
            search_window_days: Days to search ahead
            top_n: Number of recommendations to return
            start_date: Start of search window (default: now)
        
        Returns:
            Dict with recommended times and reasoning
        """
        if start_date is None:
            start_date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        end_date = start_date + datetime.timedelta(days=search_window_days)

        result = {
            'event': event_description,
            'duration_minutes': duration_minutes,
            'search_window': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'recommendations': [],
            'status': 'success'
        }

        try:
            # Fetch calendar events
            events = []
            if self.google_helper:
                events = self.google_helper.get_events(start_date, end_date)

            # Build availability blocks
            builder = AvailabilityBuilder(self.preferences)
            available_slots = builder.build_availability_blocks(
                events,
                start_date,
                end_date,
                duration_minutes
            )

            if not available_slots:
                result['status'] = 'no_slots_found'
                result['message'] = f"No available slots found for {duration_minutes}-minute event"
                return result

            # Get GPT recommendations
            if self.recommender:
                preferences_str = f"Avoid: {', '.join(self.preferences.avoid_times) or 'none'}. Preferred: {', '.join(self.preferences.preferred_times) or 'any'}"
                recommendations = self.recommender.recommend_best_times(
                    available_slots,
                    event_description,
                    preferences_str,
                    top_n
                )
                result['recommendations'] = recommendations
            else:
                # Fallback: return top slots
                result['recommendations'] = [slot.to_dict() for slot in available_slots[:top_n]]

            result['total_available_slots'] = len(available_slots)

        except Exception as e:
            result['status'] = 'error'
            result['message'] = str(e)

        return result


if __name__ == '__main__':
    # Example usage
    prefs = SchedulePreferences(
        avoid_times=['morning', 'weekend'],
        preferred_times=['afternoon'],
        work_hours_only=True
    )
    scheduler = SmartScheduler(preferences=prefs)
    
    results = scheduler.find_best_times(
        event_description="2-hour team meeting with Vusi",
        duration_minutes=120,
        search_window_days=7,
        top_n=3
    )
    
    print(json.dumps(results, indent=2, default=str))
