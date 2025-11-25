"""
Command Processor for Voice Assistant
Processes natural language commands and routes to appropriate handlers
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import re
from datetime import datetime, timedelta


class CommandType(Enum):
    """Types of voice commands"""
    BOOK_MEETING = "book_meeting"
    LIST_EVENTS = "list_events"
    SET_REMINDER = "set_reminder"
    ASK_QUESTION = "ask_question"
    SMALL_TALK = "small_talk"
    NONE = "none"


@dataclass
class Command:
    """Parsed voice command"""
    type: CommandType
    text: str
    parameters: Dict[str, Any]
    confidence: float = 0.0
    

class CommandProcessor:
    """
    Processes natural language commands from voice
    Extracts intent and parameters
    """
    
    def __init__(self):
        self.handlers: Dict[CommandType, Callable] = {}
    
    def register_handler(self, command_type: CommandType, handler: Callable) -> None:
        """Register handler for command type"""
        self.handlers[command_type] = handler
    
    def parse_command(self, text: str) -> Command:
        """
        Parse voice input and extract command
        
        Args:
            text: User's voice input
            
        Returns:
            Command object with type and parameters
        """
        text_lower = text.lower().strip()
        
        # Detect command type
        if self._matches_book_pattern(text_lower):
            command_type = CommandType.BOOK_MEETING
            params = self._extract_meeting_params(text_lower)
        elif self._matches_list_pattern(text_lower):
            command_type = CommandType.LIST_EVENTS
            params = self._extract_list_params(text_lower)
        elif self._matches_reminder_pattern(text_lower):
            command_type = CommandType.SET_REMINDER
            params = self._extract_reminder_params(text_lower)
        elif self._matches_small_talk(text_lower):
            command_type = CommandType.SMALL_TALK
            params = {}
        else:
            command_type = CommandType.ASK_QUESTION
            params = {'question': text}
        
        return Command(
            type=command_type,
            text=text,
            parameters=params,
            confidence=self._calculate_confidence(text_lower, command_type)
        )
    
    def execute_command(self, command: Command) -> Optional[Dict[str, Any]]:
        """Execute command if handler is registered"""
        handler = self.handlers.get(command.type)
        if handler:
            try:
                return handler(command)
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'message': f"Error executing command: {str(e)}"
                }
        return None
    
    def _matches_book_pattern(self, text: str) -> bool:
        """Check if text matches booking patterns"""
        patterns = [
            r'\b(?:book|schedule|create|set up|add)\s+(?:a\s+)?(?:meeting|event|appointment)',
            r'\bmeet(?:ing)?\s+(?:with|on)',
            r'\b(?:new|create)\s+event',
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _matches_list_pattern(self, text: str) -> bool:
        """Check if text matches event listing patterns"""
        patterns = [
            r'\b(?:what|show|list|display)\s+(?:my\s+)?(?:events|meetings|calendar|schedule)',
            r'\bwhat(?:\'s|\s+is)\s+(?:on|scheduled|on my calendar)',
            r'\bany\s+(?:meetings|events)(?:\s+(?:today|tomorrow|this week))?',
            r'\bupcoming\s+(?:meetings|events)',
            r'\bmy\s+(?:events|meetings|schedule|calendar)',
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _matches_reminder_pattern(self, text: str) -> bool:
        """Check if text matches reminder patterns"""
        patterns = [
            r'\b(?:set|create|add)\s+(?:a\s+)?reminder',
            r'\bremind\s+me(?:\s+(?:to|at|on))',
            r'\b(?:remind|schedule a reminder)',
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _matches_small_talk(self, text: str) -> bool:
        """Check if text is small talk"""
        patterns = [
            r'\b(?:hello|hi|hey)\b',
            r'\b(?:good\s+(?:morning|afternoon|evening))',
            r'\b(?:thanks?|thank you)',
            r'\b(?:how are you|how\'s it going)',
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _extract_meeting_params(self, text: str) -> Dict[str, Any]:
        """Extract meeting parameters from text"""
        params = {}
        
        # Extract title (words after "about", "for", "called")
        title_match = re.search(r'(?:about|for|called|titled)\s+([^.,]+?)(?:\s+(?:with|on|at|tomorrow|today|monday)|\.|$)', text)
        if title_match:
            params['title'] = title_match.group(1).strip()
        
        # Extract time
        time_match = re.search(r'(?:at\s+)?(\d{1,2}):?(\d{2})?\s*(?:am|pm)?', text)
        if time_match:
            hour = time_match.group(1)
            minute = time_match.group(2) or "00"
            am_pm = re.search(r'(am|pm)', text)
            if am_pm:
                period = am_pm.group(1)
                if period.lower() == 'pm' and int(hour) != 12:
                    hour = str(int(hour) + 12)
                elif period.lower() == 'am' and hour == '12':
                    hour = '00'
            params['time'] = f"{int(hour):02d}:{minute}"
        
        # Extract date
        date_keywords = {
            'today': 0,
            'tomorrow': 1,
            'monday': 'MONDAY',
            'tuesday': 'TUESDAY',
            'wednesday': 'WEDNESDAY',
            'thursday': 'THURSDAY',
            'friday': 'FRIDAY',
            'saturday': 'SATURDAY',
            'sunday': 'SUNDAY',
        }
        for keyword, offset in date_keywords.items():
            if keyword in text:
                if isinstance(offset, int):
                    date = (datetime.now() + timedelta(days=offset)).strftime('%Y-%m-%d')
                    params['date'] = date
                else:
                    params['date'] = keyword.upper()
                break
        
        # Extract duration
        duration_match = re.search(r'(\d+)\s*(?:minutes?|mins?|hours?|hrs?)', text)
        if duration_match:
            value = int(duration_match.group(1))
            if 'hour' in text or 'hr' in text:
                value *= 60
            params['duration'] = value
        
        # Extract attendees
        attendees_match = re.search(r'with\s+([^.]+?)(?:\s+(?:at|on|tomorrow|today|this)|\.|$)', text)
        if attendees_match:
            attendees_str = attendees_match.group(1)
            attendees = re.split(r'\s+and\s+|,\s*', attendees_str)
            params['attendees'] = [a.strip() for a in attendees if a.strip()]
        
        return params
    
    def _extract_list_params(self, text: str) -> Dict[str, Any]:
        """Extract list/query parameters"""
        params = {'filter': None}
        
        # Extract date filter
        if 'today' in text:
            params['filter'] = 'today'
        elif 'tomorrow' in text:
            params['filter'] = 'tomorrow'
        elif 'this week' in text or 'this week' in text:
            params['filter'] = 'this_week'
        elif 'next week' in text:
            params['filter'] = 'next_week'
        elif 'this month' in text:
            params['filter'] = 'this_month'
        
        return params
    
    def _extract_reminder_params(self, text: str) -> Dict[str, Any]:
        """Extract reminder parameters"""
        # Similar to meeting extraction but simpler
        params = {}
        
        # Extract reminder text
        reminder_match = re.search(r'(?:remind me to|reminder to|remind me about)\s+([^.]+?)(?:\s+(?:at|on|tomorrow|today)|$)', text)
        if reminder_match:
            params['title'] = reminder_match.group(1).strip()
        
        # Extract time/date (same as meetings)
        time_match = re.search(r'at\s+(\d{1,2}):?(\d{2})?\s*(?:am|pm)?', text)
        if time_match:
            hour = time_match.group(1)
            minute = time_match.group(2) or "00"
            params['time'] = f"{int(hour):02d}:{minute}"
        
        # Extract date
        if 'today' in text:
            params['date'] = 'TODAY'
        elif 'tomorrow' in text:
            params['date'] = 'TOMORROW'
        
        return params
    
    def _calculate_confidence(self, text: str, command_type: CommandType) -> float:
        """Calculate confidence score for parsed command"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on completeness of command
        if command_type == CommandType.BOOK_MEETING:
            # Check for required parameters
            if 'at' in text or ':' in text:  # Has time
                confidence += 0.1
            if any(word in text for word in ['tomorrow', 'today', 'monday', 'tuesday']):  # Has date
                confidence += 0.1
            if any(word in text for word in ['with', 'meeting about']):  # Has attendees/topic
                confidence += 0.1
        
        elif command_type == CommandType.LIST_EVENTS:
            confidence = 0.9  # Usually clear intent
        
        elif command_type == CommandType.SET_REMINDER:
            confidence = 0.85
        
        return min(confidence, 1.0)
