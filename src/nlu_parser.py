"""
Advanced Natural Language Parser for Voice Assistant Calendar

Extracts event details (date, time, title, attendees) from voice input
in ANY word order using pattern matching and context analysis.

Examples:
- "book Friday 2PM movie date with John" → {date: Fri, time: 14:00, title: movie date, attendees: John}
- "movie date with John Friday 2PM" → same
- "2PM Friday movie with John" → same
- "book meeting with Sarah tomorrow at 3" → {date: tomorrow, time: 15:00, attendees: Sarah}
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import dateparser


class EventDetailExtractor:
    """Extracts structured event information from natural language."""
    
    # Attendee prefixes
    ATTENDEE_PATTERNS = [
        r'with\s+(.+?)(?:\s+(?:at|on|tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d+|next|this|in)|\s*$)',
        r'(?:and|plus)\s+(.+?)(?:\s+(?:at|on|tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d+|next|this|in)|\s*$)',
        r'attend(?:ee)?s?:?\s+(.+?)(?:\s+(?:at|on|tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d+|next|this|in)|\s*$)',
        r'(?:invite|add|call)\s+(.+?)(?:\s+(?:at|on|tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d+|next|this|in)|\s*$)',
    ]
    
    # Time patterns (flexible)
    TIME_PATTERNS = [
        r'(\d{1,2}):?(\d{2})?\s*([apAP]\.?[mM]\.?)?',  # 2:30pm, 2:30 pm, 14:30, etc
        r'\b(morning|afternoon|evening|night|noon|midnight)\b',
        r'\b(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.)\b',
    ]
    
    # Date patterns (relative)
    RELATIVE_DATE_KEYWORDS = {
        'today': 0,
        'tomorrow': 1,
        'tonight': 0,
        'yesterday': -1,
        'next monday': 1,  # adjusted based on current day
        'next tuesday': 2,
        'next wednesday': 3,
        'next thursday': 4,
        'next friday': 5,
        'next saturday': 6,
        'next sunday': 0,
        'this week': 0,
        'next week': 7,
        'in 2 days': 2,
        'in 3 days': 3,
    }
    
    DAY_NAMES = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    MONTH_NAMES = ['january', 'february', 'march', 'april', 'may', 'june', 
                   'july', 'august', 'september', 'october', 'november', 'december']
    
    def __init__(self):
        """Initialize the extractor."""
        pass
    
    def extract_all(self, voice_input: str) -> Dict:
        """
        Extract all event details from voice input.
        
        Args:
            voice_input: Raw voice command text
            
        Returns:
            Dict with keys: date, time, title, attendees, missing_keys
        """
        result = {
            'date': None,
            'time': None,
            'title': None,
            'attendees': [],
            'missing_keys': []
        }
        
        # Remove common prefixes
        clean_input = self._clean_input(voice_input)
        
        # Extract each component
        result['attendees'] = self.extract_attendees(clean_input)
        clean_input = self._remove_attendees(clean_input)
        
        result['date'] = self.extract_date(clean_input)
        clean_input = self._remove_dates(clean_input)
        
        result['time'] = self.extract_time(clean_input)
        clean_input = self._remove_times(clean_input)
        
        # Remaining text is the title
        result['title'] = self._extract_title(clean_input)
        
        # Track what's missing
        if not result['date']:
            result['missing_keys'].append('date')
        if not result['time']:
            result['missing_keys'].append('time')
        if not result['title']:
            result['missing_keys'].append('title')
        
        return result
    
    def _clean_input(self, text: str) -> str:
        """Remove command prefixes like 'book', 'schedule', etc."""
        prefixes = r'^(book|schedule|add|create|set\s+up|let\'s)\s+'
        return re.sub(prefixes, '', text, flags=re.IGNORECASE).strip()
    
    def extract_attendees(self, text: str) -> List[str]:
        """Extract attendee names from text."""
        attendees = []
        
        for pattern in self.ATTENDEE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                attendee_text = match.group(1)
                if attendee_text:
                    # Parse multiple attendees separated by "and", "or", ","
                    names = re.split(r'\s+(?:and|or|,)\s+', attendee_text)
                    for name in names:
                        name = name.strip()
                        # Clean up: remove articles, prepositions
                        name = re.sub(r'(?:^(a|an|the)\s+|at\s+.*$)', '', name, flags=re.IGNORECASE)
                        if name and len(name) > 1:
                            attendees.append(name)
        
        return list(set(attendees))  # Remove duplicates
    
    def extract_date(self, text: str) -> Optional[str]:
        """
        Extract date from text.
        Returns: YYYY-MM-DD format or None
        """
        # Try absolute dates first (MM/DD, DD/MM, YYYY-MM-DD)
        absolute_patterns = [
            r'(\d{4}[-/]\d{2}[-/]\d{2})',  # 2024-12-25
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',  # 12/25/2024 or 25-12-2024
        ]
        
        for pattern in absolute_patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1).replace('/', '-')
                try:
                    parsed = dateparser.parse(date_str)
                    if parsed:
                        return parsed.strftime('%Y-%m-%d')
                except:
                    pass
        
        # Try day names (Monday, Friday, etc)
        for day_name in self.DAY_NAMES:
            if re.search(r'\b' + day_name + r'\b', text, re.IGNORECASE):
                return self._get_next_day_date(day_name)
        
        # Try relative dates
        for keyword, offset in self.RELATIVE_DATE_KEYWORDS.items():
            if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
                target_date = datetime.now() + timedelta(days=offset)
                return target_date.strftime('%Y-%m-%d')
        
        # Try text parsing with dateparser
        try:
            parsed = dateparser.parse(text, settings={'PREFER_DATES_FROM': 'current_period'})
            if parsed:
                return parsed.strftime('%Y-%m-%d')
        except:
            pass
        
        return None
    
    def extract_time(self, text: str) -> Optional[str]:
        """
        Extract time from text.
        Returns: HH:MM format or None
        """
        # Pattern: HH:MM or H:MM with optional am/pm
        time_pattern = r'(\d{1,2}):?(\d{2})?\s*(?:([apAP]\.?[mM]\.?)|([apAP][mM]))?'
        
        match = re.search(time_pattern, text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            meridiem = match.group(3) or match.group(4)
            
            # Convert to 24-hour format if pm specified
            if meridiem and meridiem.lower().startswith('p'):
                if hour != 12:
                    hour += 12
            elif meridiem and meridiem.lower().startswith('a'):
                if hour == 12:
                    hour = 0
            
            return f"{hour:02d}:{minute:02d}"
        
        # Try text-based times
        time_keywords = {
            'morning': '09:00',
            'afternoon': '14:00',
            'evening': '18:00',
            'night': '20:00',
            'noon': '12:00',
            'midnight': '00:00',
        }
        
        for keyword, time_val in time_keywords.items():
            if re.search(r'\b' + keyword + r'\b', text, re.IGNORECASE):
                return time_val
        
        return None
    
    def _extract_title(self, text: str) -> Optional[str]:
        """Extract event title from remaining text."""
        # Remove extra whitespace and clean up
        title = text.strip()
        
        # Remove common filler words
        title = re.sub(r'\b(a|an|the|for|to|with|at|on|by)\b', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s+', ' ', title).strip()
        
        # If we have something meaningful, return it
        if title and len(title) > 2:
            return title
        
        return None
    
    def _remove_attendees(self, text: str) -> str:
        """Remove attendee mentions from text."""
        for pattern in self.ATTENDEE_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        return text
    
    def _remove_dates(self, text: str) -> str:
        """Remove date mentions from text."""
        # Remove day names
        for day in self.DAY_NAMES:
            text = re.sub(r'\b' + day + r'\b', '', text, flags=re.IGNORECASE)
        
        # Remove relative dates
        for keyword in self.RELATIVE_DATE_KEYWORDS.keys():
            text = re.sub(r'\b' + re.escape(keyword) + r'\b', '', text, flags=re.IGNORECASE)
        
        # Remove date patterns
        text = re.sub(r'\d{1,2}[-/]\d{1,2}(?:[-/]\d{2,4})?', '', text)
        
        return text
    
    def _remove_times(self, text: str) -> str:
        """Remove time mentions from text."""
        # Remove time patterns
        text = re.sub(r'\d{1,2}:?\d{2}?\s*(?:[apAP]\.?[mM]\.?)?', '', text, flags=re.IGNORECASE)
        
        # Remove time keywords
        time_keywords = ['morning', 'afternoon', 'evening', 'night', 'noon', 'midnight']
        for keyword in time_keywords:
            text = re.sub(r'\b' + keyword + r'\b', '', text, flags=re.IGNORECASE)
        
        return text
    
    def _get_next_day_date(self, day_name: str) -> str:
        """Get the date for the next occurrence of a day name."""
        day_name = day_name.lower()
        day_num = self.DAY_NAMES.index(day_name)
        
        today = datetime.now()
        today_weekday = today.weekday()  # 0=Monday, 6=Sunday
        
        # Days until target day
        days_ahead = day_num - today_weekday
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        target_date = today + timedelta(days=days_ahead)
        return target_date.strftime('%Y-%m-%d')


class MissingDetailPrompter:
    """Interactively prompts user for missing event details."""
    
    def __init__(self, voice_handler=None):
        """
        Initialize the prompter.
        
        Args:
            voice_handler: Optional VoiceOutput instance for speaking prompts
        """
        self.voice_handler = voice_handler
    
    def prompt_missing(self, missing_keys: List[str], extracted: Dict) -> Dict:
        """
        Prompt user for missing details.
        
        Args:
            missing_keys: List of missing keys ['date', 'time', 'title', ...]
            extracted: Dict of already-extracted details
            
        Returns:
            Updated dict with filled-in details
        """
        for key in missing_keys:
            if key == 'date':
                extracted['date'] = self._prompt_date()
            elif key == 'time':
                extracted['time'] = self._prompt_time()
            elif key == 'title':
                extracted['title'] = self._prompt_title()
            elif key == 'attendees':
                attendees = self._prompt_attendees()
                extracted['attendees'] = attendees
        
        return extracted
    
    def _prompt_date(self) -> str:
        """Prompt for date input."""
        prompt = "What date would you like to book? (e.g., 'tomorrow', 'Friday', '12/25')"
        return self._get_input(prompt, "date")
    
    def _prompt_time(self) -> str:
        """Prompt for time input."""
        prompt = "What time? (e.g., '2 PM', '14:00', '2:30')"
        return self._get_input(prompt, "time")
    
    def _prompt_title(self) -> str:
        """Prompt for event title."""
        prompt = "What should I call this event? (e.g., 'Meeting with John', 'Dentist appointment')"
        return self._get_input(prompt, "title")
    
    def _prompt_attendees(self) -> List[str]:
        """Prompt for attendee names."""
        prompt = "Who should attend? (e.g., 'John, Sarah and Mike' or 'none')"
        response = self._get_input(prompt, "attendees")
        
        if response.lower() in ['none', 'no one', 'nobody']:
            return []
        
        # Parse attendee names
        names = re.split(r'\s+(?:and|,|\+)\s+', response)
        return [name.strip() for name in names if name.strip()]
    
    def _get_input(self, prompt: str, input_type: str) -> str:
        """
        Get user input via voice or text.
        
        Args:
            prompt: The prompt to display/speak
            input_type: Type of input being requested (for parsing)
            
        Returns:
            User's response
        """
        # Display the prompt
        print(f"\n📢 {prompt}")
        
        # Speak the prompt if voice available
        if self.voice_handler and self.voice_handler.is_available():
            self.voice_handler.speak(prompt, wait=False)
        
        # Get user input
        try:
            user_input = input("You: ").strip()
        except EOFError:
            # Fallback if input fails
            user_input = ""
        
        # Parse the input based on type
        if input_type == "date":
            extractor = EventDetailExtractor()
            parsed_date = extractor.extract_date(user_input)
            if parsed_date:
                return parsed_date
            # If parsing fails, ask again
            print("⚠️  Couldn't parse that date. Please try again.")
            return self._prompt_date()
        
        elif input_type == "time":
            extractor = EventDetailExtractor()
            parsed_time = extractor.extract_time(user_input)
            if parsed_time:
                return parsed_time
            print("⚠️  Couldn't parse that time. Please try again.")
            return self._prompt_time()
        
        else:
            # For title and attendees, just return the input as-is
            return user_input


# Test the parser
if __name__ == "__main__":
    extractor = EventDetailExtractor()
    prompter = MissingDetailPrompter()
    
    # Test cases
    test_inputs = [
        "book Friday 2PM movie date with John",
        "movie date with John Friday 2PM",
        "2PM Friday meeting with Sarah and Mike",
        "book meeting tomorrow at 3",
        "calendar event next Monday with team",
        "schedule dentist appointment on 12/25 at 10am",
    ]
    
    for test_input in test_inputs:
        print(f"\n{'='*60}")
        print(f"Input: {test_input}")
        result = extractor.extract_all(test_input)
        print(f"Extracted: {result}")
        
        if result['missing_keys']:
            print(f"Missing: {result['missing_keys']}")
