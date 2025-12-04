"""
Google Calendar Service Wrapper

Clean separation of Google Calendar API logic.
This module handles:
- Authentication and token management
- Fetching events
- Creating events
- Deleting events
- Updating events

All calendar operations go through here.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """Wrapper for Google Calendar API"""
    
    SCOPES = [
        'openid',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/calendar'
    ]
    
    def __init__(self, client_secret_file: str, credentials: Optional[Credentials] = None):
        """
        Initialize Google Calendar service.
        
        Args:
            client_secret_file (str): Path to Google OAuth client secret JSON
            credentials (Credentials): Optional pre-existing credentials
        """
        self.client_secret_file = client_secret_file
        self.credentials = credentials
        self.service = None
        
        if self.credentials:
            self._build_service()
    
    def _build_service(self):
        """Build the Google Calendar API service"""
        if self.credentials:
            self.service = build('calendar', 'v3', credentials=self.credentials)
    
    def set_credentials(self, credentials: Credentials):
        """
        Set credentials and rebuild service.
        
        Args:
            credentials (Credentials): OAuth credentials
        """
        self.credentials = credentials
        self._build_service()
    
    def get_events(
        self,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Fetch events from Google Calendar.
        
        Args:
            time_min (datetime): Start time (default: now)
            time_max (datetime): End time (default: 30 days from now)
            max_results (int): Maximum results to return
        
        Returns:
            List[Dict]: List of events with id, title, start, date, time
        """
        
        if not self.service:
            logger.error("Service not initialized")
            return []
        
        if not time_min:
            time_min = datetime.utcnow()
        
        if not time_max:
            time_max = datetime.utcnow() + timedelta(days=30)
        
        try:
            logger.info(f"📅 Fetching events from {time_min.date()} to {time_max.date()}")
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = []
            for event in events_result.get('items', []):
                start = event['start'].get('dateTime', event['start'].get('date'))
                events.append({
                    'id': event['id'],
                    'title': event.get('summary', 'Untitled'),
                    'start': start,
                    'date': start.split('T')[0] if 'T' in start else start,
                    'time': start.split('T')[1][:5] if 'T' in start else '00:00',
                    'description': event.get('description', ''),
                    'attendees': [a.get('email') for a in event.get('attendees', [])]
                })
            
            logger.info(f"✅ Found {len(events)} events")
            return events
        
        except HttpError as e:
            logger.error(f"Calendar API error: {str(e)}")
            return []
    
    def create_event(
        self,
        title: str,
        date: str,
        time: str = "09:00",
        duration: int = 60,
        description: str = "",
        attendees: Optional[List[str]] = None,
        timezone: str = "UTC"
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new event on Google Calendar.
        
        Args:
            title (str): Event title
            date (str): Date in YYYY-MM-DD format
            time (str): Time in HH:MM format (default: 09:00)
            duration (int): Duration in minutes (default: 60)
            description (str): Event description
            attendees (List[str]): List of attendee emails
            timezone (str): Timezone (default: UTC)
        
        Returns:
            Dict: Created event with id, or None if failed
        """
        
        if not self.service:
            logger.error("Service not initialized")
            return None
        
        try:
            # Parse time
            hour, minute = map(int, time.split(':'))
            
            # Create start time
            start_time = f"{date}T{time}:00"
            
            # Calculate end time
            end_hour = hour + (duration // 60)
            end_minute = minute + (duration % 60)
            if end_minute >= 60:
                end_hour += 1
                end_minute -= 60
            
            end_time = f"{date}T{end_hour:02d}:{end_minute:02d}:00"
            
            # Build event body
            event_body = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time,
                    'timeZone': timezone
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': timezone
                }
            }
            
            # Add attendees if provided
            if attendees:
                event_body['attendees'] = [{'email': email} for email in attendees]
            
            logger.info(f"📝 Creating event: {title} on {date} at {time}")
            
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event_body
            ).execute()
            
            logger.info(f"✅ Event created with ID: {created_event['id']}")
            
            return {
                'id': created_event['id'],
                'title': created_event['summary'],
                'start': created_event['start'].get('dateTime'),
                'message': f"✅ Event '{title}' created for {date} at {time}"
            }
        
        except HttpError as e:
            logger.error(f"Failed to create event: {str(e)}")
            return None
    
    def delete_event(self, event_id: str) -> bool:
        """
        Delete an event from Google Calendar.
        
        Args:
            event_id (str): The event ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        
        if not self.service:
            logger.error("Service not initialized")
            return False
        
        try:
            logger.info(f"🗑️ Deleting event: {event_id}")
            
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            logger.info(f"✅ Event deleted")
            return True
        
        except HttpError as e:
            logger.error(f"Failed to delete event: {str(e)}")
            return False
    
    def find_event_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Find an event by title (partial match).
        
        Args:
            title (str): Event title to search for
        
        Returns:
            Dict: Event if found, None otherwise
        """
        
        events = self.get_events(max_results=100)
        
        title_lower = title.lower()
        for event in events:
            if title_lower in event['title'].lower():
                return event
        
        return None
