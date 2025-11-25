"""
Calendar Conflict Detection and Resolution
Detects overlapping events and suggests alternatives
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import pytz


@dataclass
class TimeSlot:
    """Represents a time slot in the calendar"""
    start: datetime
    end: datetime
    event_id: str = ""
    event_title: str = ""
    
    def overlaps_with(self, other: 'TimeSlot') -> bool:
        """Check if this slot overlaps with another"""
        return self.start < other.end and self.end > other.start
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'start': self.start.isoformat(),
            'end': self.end.isoformat(),
            'event_id': self.event_id,
            'event_title': self.event_title
        }


class ConflictDetector:
    """
    Detects and resolves calendar conflicts
    """
    
    def __init__(self, timezone: str = 'Africa/Johannesburg'):
        self.timezone = pytz.timezone(timezone)
    
    def detect_conflicts(
        self, 
        proposed_slot: TimeSlot, 
        existing_events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect conflicts between proposed meeting and existing events
        
        Args:
            proposed_slot: The new meeting time slot
            existing_events: List of existing calendar events
            
        Returns:
            List of conflicting events
        """
        conflicts = []
        
        for event in existing_events:
            try:
                # Parse event times
                start_str = event.get('start', {}).get('dateTime') or event.get('start', {}).get('date')
                end_str = event.get('end', {}).get('dateTime') or event.get('end', {}).get('date')
                
                if not start_str or not end_str:
                    continue
                
                # Parse with timezone
                event_start = self._parse_datetime(start_str)
                event_end = self._parse_datetime(end_str)
                
                existing_slot = TimeSlot(event_start, event_end, event.get('id', ''), event.get('summary', 'Untitled'))
                
                # Check for overlap
                if proposed_slot.overlaps_with(existing_slot):
                    conflicts.append({
                        'event_id': existing_slot.event_id,
                        'event_title': existing_slot.event_title,
                        'start': event_start.isoformat(),
                        'end': event_end.isoformat(),
                        'duration_minutes': int((event_end - event_start).total_seconds() / 60)
                    })
            except Exception as e:
                print(f"Error parsing event: {e}")
                continue
        
        return conflicts
    
    def suggest_alternatives(
        self,
        proposed_slot: TimeSlot,
        existing_events: List[Dict[str, Any]],
        duration_minutes: int = 30,
        max_suggestions: int = 3,
        search_days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Suggest alternative time slots without conflicts
        
        Args:
            proposed_slot: The original proposed time
            existing_events: List of existing calendar events
            duration_minutes: Duration of proposed meeting
            max_suggestions: Maximum suggestions to return
            search_days: How many days ahead to search
            
        Returns:
            List of suggested time slots
        """
        suggestions = []
        current_slot = TimeSlot(proposed_slot.start, proposed_slot.end)
        
        # Search through next N days
        for days_offset in range(search_days):
            # Try different time slots throughout the day
            test_date = proposed_slot.start + timedelta(days=days_offset)
            
            # Business hours: 8 AM to 5 PM
            for hour in range(8, 17):
                for minute in [0, 30]:  # 30-min intervals
                    test_start = test_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    test_end = test_start + timedelta(minutes=duration_minutes)
                    test_slot = TimeSlot(test_start, test_end)
                    
                    # Check if this slot is free
                    conflicts = self.detect_conflicts(test_slot, existing_events)
                    
                    if not conflicts:
                        suggestions.append({
                            'start': test_start.isoformat(),
                            'end': test_end.isoformat(),
                            'date_str': test_start.strftime('%A, %B %d'),
                            'time_str': test_start.strftime('%I:%M %p'),
                            'reason': 'Available' if days_offset == 0 else f'Available in {days_offset} days'
                        })
                        
                        if len(suggestions) >= max_suggestions:
                            return suggestions
        
        return suggestions
    
    def resolve_conflict(
        self,
        proposed_slot: TimeSlot,
        conflicts: List[Dict[str, Any]],
        resolution_type: str = "move"
    ) -> Dict[str, Any]:
        """
        Handle conflict resolution
        
        Args:
            proposed_slot: The proposed time slot
            conflicts: List of conflicting events
            resolution_type: How to resolve - "move", "cancel", "overwrite"
            
        Returns:
            Resolution action details
        """
        if resolution_type == "move":
            # Find alternative time
            return {
                'action': 'move',
                'type': 'need_alternatives',
                'message': f"Your proposed time conflicts with {len(conflicts)} event(s). Would you like me to suggest alternative times?",
                'conflicting_events': conflicts
            }
        
        elif resolution_type == "cancel":
            return {
                'action': 'cancel',
                'type': 'cancelled',
                'message': f"Cancelled booking. Conflicting with: {', '.join([c['event_title'] for c in conflicts])}",
                'conflicting_events': conflicts
            }
        
        elif resolution_type == "overwrite":
            return {
                'action': 'overwrite',
                'type': 'confirmed',
                'message': f"Warning: This will overwrite {len(conflicts)} event(s). Are you sure?",
                'conflicting_events': conflicts,
                'warning': True
            }
        
        else:
            return {
                'action': 'unknown',
                'type': 'error',
                'message': "Unknown conflict resolution type"
            }
    
    def _parse_datetime(self, dt_str: str) -> datetime:
        """
        Parse datetime string (ISO format or date-only)
        
        Args:
            dt_str: DateTime string to parse
            
        Returns:
            datetime object in specified timezone
        """
        try:
            # Try parsing as ISO datetime
            if 'T' in dt_str:
                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = self.timezone.localize(dt)
                return dt.astimezone(self.timezone)
            else:
                # Parse as date only
                dt = datetime.strptime(dt_str, '%Y-%m-%d')
                return self.timezone.localize(dt)
        except Exception:
            # Fallback to current time
            return self.timezone.localize(datetime.now())
    
    def get_availability_summary(
        self,
        existing_events: List[Dict[str, Any]],
        date_str: str,
        timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get availability summary for a given date
        
        Args:
            existing_events: List of calendar events
            date_str: Date to check (YYYY-MM-DD)
            timezone: Optional timezone override
            
        Returns:
            Summary of free/busy times
        """
        tz = pytz.timezone(timezone or self.timezone)
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
        target_date = tz.localize(target_date)
        
        # Get events for this date
        day_events = []
        for event in existing_events:
            try:
                start_str = event.get('start', {}).get('dateTime') or event.get('start', {}).get('date')
                if start_str:
                    event_start = self._parse_datetime(start_str)
                    if event_start.date() == target_date.date():
                        end_str = event.get('end', {}).get('dateTime') or event.get('end', {}).get('date')
                        event_end = self._parse_datetime(end_str)
                        day_events.append({
                            'start': event_start,
                            'end': event_end,
                            'title': event.get('summary', 'Untitled')
                        })
            except Exception:
                continue
        
        # Sort by start time
        day_events.sort(key=lambda x: x['start'])
        
        # Calculate free slots
        free_slots = []
        work_start = target_date.replace(hour=8, minute=0)
        work_end = target_date.replace(hour=17, minute=0)
        
        current_time = work_start
        for event in day_events:
            if event['start'] > current_time:
                free_slots.append({
                    'start': current_time.isoformat(),
                    'end': event['start'].isoformat(),
                    'duration_minutes': int((event['start'] - current_time).total_seconds() / 60)
                })
            current_time = max(current_time, event['end'])
        
        if current_time < work_end:
            free_slots.append({
                'start': current_time.isoformat(),
                'end': work_end.isoformat(),
                'duration_minutes': int((work_end - current_time).total_seconds() / 60)
            })
        
        return {
            'date': date_str,
            'total_events': len(day_events),
            'events': day_events,
            'free_slots': free_slots,
            'is_fully_booked': len(free_slots) == 0
        }
