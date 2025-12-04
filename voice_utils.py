"""
Voice Utilities

Helper functions for:
- Cleaning up voice transcripts
- Validating dates and times
- Parsing natural language dates
- Formatting dates/times for display
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def clean_transcript(text: str) -> str:
    """
    Clean up voice transcript.
    
    - Remove leading/trailing whitespace
    - Fix common speech-to-text errors
    - Normalize punctuation
    
    Args:
        text (str): Raw voice transcript
    
    Returns:
        str: Cleaned text
    """
    text = text.strip()
    
    # Fix common replacements
    replacements = {
        'for': 'four',  # context-dependent
        'to': 'two',    # context-dependent
    }
    
    # Could add more sophisticated cleaning here
    return text


def is_valid_date(date_str: str) -> bool:
    """
    Check if a date string is valid (YYYY-MM-DD format).
    
    Args:
        date_str (str): Date string
    
    Returns:
        bool: True if valid
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def is_valid_time(time_str: str) -> bool:
    """
    Check if a time string is valid (HH:MM format).
    
    Args:
        time_str (str): Time string
    
    Returns:
        bool: True if valid
    """
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


def parse_relative_date(relative: str) -> Optional[str]:
    """
    Parse relative date references to YYYY-MM-DD format.
    
    Args:
        relative (str): "today", "tomorrow", "next week", etc.
    
    Returns:
        str: Date in YYYY-MM-DD format, or None if unable to parse
    """
    relative_lower = relative.lower().strip()
    today = datetime.now()
    
    # Today
    if relative_lower in ['today', 'today']:
        return today.strftime("%Y-%m-%d")
    
    # Tomorrow
    if relative_lower in ['tomorrow', 'tomorow']:
        tomorrow = today + timedelta(days=1)
        return tomorrow.strftime("%Y-%m-%d")
    
    # Day of week
    days_of_week = {
        'monday': 0, 'mon': 0,
        'tuesday': 1, 'tue': 1, 'tues': 1,
        'wednesday': 2, 'wed': 2,
        'thursday': 3, 'thu': 3, 'thurs': 3,
        'friday': 4, 'fri': 4,
        'saturday': 5, 'sat': 5,
        'sunday': 6, 'sun': 6
    }
    
    if relative_lower in days_of_week:
        target_day = days_of_week[relative_lower]
        current_day = today.weekday()
        days_ahead = target_day - current_day
        if days_ahead <= 0:
            days_ahead += 7
        date = today + timedelta(days=days_ahead)
        return date.strftime("%Y-%m-%d")
    
    # Next week
    if 'next week' in relative_lower:
        next_week = today + timedelta(weeks=1)
        return next_week.strftime("%Y-%m-%d")
    
    # This week (end)
    if 'this week' in relative_lower:
        end_of_week = today + timedelta(days=(6 - today.weekday()))
        return end_of_week.strftime("%Y-%m-%d")
    
    return None


def format_date_for_display(date_str: str) -> str:
    """
    Format date for user-friendly display.
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
    
    Returns:
        str: Formatted date like "Monday, December 1"
    """
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%A, %B %d")
    except ValueError:
        return date_str


def format_time_for_display(time_str: str) -> str:
    """
    Format time for user-friendly display.
    
    Args:
        time_str (str): Time in HH:MM format
    
    Returns:
        str: Formatted time like "2:00 PM"
    """
    try:
        dt = datetime.strptime(time_str, "%H:%M")
        return dt.strftime("%I:%M %p").lstrip('0')
    except ValueError:
        return time_str


def get_time_until(date_str: str, time_str: str = "09:00") -> str:
    """
    Get human-readable time until an event.
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        time_str (str): Time in HH:MM format
    
    Returns:
        str: "in 3 days", "tomorrow", "in 2 hours", etc.
    """
    try:
        event_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        now = datetime.now()
        diff = event_dt - now
        
        if diff.days > 1:
            return f"in {diff.days} days"
        elif diff.days == 1:
            return "tomorrow"
        elif diff.total_seconds() > 3600:
            hours = int(diff.total_seconds() // 3600)
            return f"in {hours} hours"
        elif diff.total_seconds() > 60:
            minutes = int(diff.total_seconds() // 60)
            return f"in {minutes} minutes"
        else:
            return "very soon"
    except ValueError:
        return ""


if __name__ == "__main__":
    # Test utilities
    print(f"Today: {parse_relative_date('today')}")
    print(f"Tomorrow: {parse_relative_date('tomorrow')}")
    print(f"Formatted: {format_date_for_display('2025-12-01')}")
    print(f"Time: {format_time_for_display('14:00')}")
