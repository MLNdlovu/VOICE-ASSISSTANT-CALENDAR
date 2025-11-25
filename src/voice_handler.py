"""
Voice Command Integration Module

This module handles voice input, speech recognition, command parsing, and voice output.
It converts spoken commands into executable actions for the Voice Assistant Calendar system
and provides AI voice responses back to the user.
"""

import re
from typing import Optional, Tuple
from datetime import datetime, timedelta
try:
    from dateutil import parser as du_parser
    DATEUTIL_AVAILABLE = True
except Exception:
    du_parser = None
    DATEUTIL_AVAILABLE = False

try:
    import speech_recognition as sr
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False


class VoiceOutput:
    """
    Handles text-to-speech voice output using pyttsx3.
    Speaks AI responses back to the user with configurable voice settings.
    """
    
    def __init__(self, rate: int = 150, volume: float = 0.9):
        """
        Initialize the voice output engine.
        
        Parameters:
        - rate: Speech rate (words per minute). Default: 150.
        - volume: Volume level (0.0 to 1.0). Default: 0.9.
        """
        self.rate = rate
        self.volume = volume
        
        if not TTS_AVAILABLE:
            print("[WARN] pyttsx3 not installed.")
            print("   Install with: pip install pyttsx3")
            self.engine = None
        else:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate', self.rate)
                self.engine.setProperty('volume', self.volume)
                print("[INFO] Voice output engine initialized.")
            except Exception as e:
                print(f"[WARN] Text-to-speech initialization failed: {e}")
                self.engine = None
    
    def is_available(self) -> bool:
        """Check if text-to-speech is available and working."""
        return TTS_AVAILABLE and self.engine is not None
    
    def speak(self, text: str, wait: bool = True) -> None:
        """
        Speak the given text using text-to-speech.
        
        Parameters:
        - text: The text to speak.
        - wait: If True, wait for speech to finish before returning. Default: True.
        """
        if not self.is_available():
            return
        
        try:
            self.engine.say(text)
            if wait:
                self.engine.runAndWait()
            else:
                # Start speaking without blocking
                self.engine.startLoop(False)
        except Exception as e:
            print(f"❌ Error during text-to-speech: {e}")
    
    def set_rate(self, rate: int) -> None:
        """Set the speech rate (words per minute)."""
        if self.is_available():
            self.rate = rate
            self.engine.setProperty('rate', rate)
    
    def set_volume(self, volume: float) -> None:
        """Set the volume level (0.0 to 1.0)."""
        if self.is_available() and 0.0 <= volume <= 1.0:
            self.volume = volume
            self.engine.setProperty('volume', volume)
    
    def speak_response(self, response: str) -> None:
        """
        Speak a formatted AI response with visual feedback.
        
        Parameters:
        - response: The response text to speak.
        """
        if self.is_available():
            print(f"[AI] {response}")
            self.speak(response)
        else:
            print(f"[AI] {response}")


class VoiceCommandParser:
    EVENTS_FOR_DAY_PATTERNS = [
        r"what are my events for the day",
        r"what are my events today",
        r"show my events for the day",
        r"show my events today",
        r"list my events for the day",
        r"list my events today",
        r"events for the day",
        r"events today",
        r"meetings for the day",
        r"meetings today",
        r"appointments for the day",
        r"appointments today",
        r"what do i have (today|for the day)",
        r"what's on my calendar (today|for the day)",
    ]
    """
    Parses natural language voice commands and extracts relevant parameters.
    
    Supports commands like:
    - "Book a slot on 2024-03-01 at 10:00 for Python help"
    - "Cancel my booking on 2024-03-01 at 10:00"
    - "Show me upcoming events"
    - "Show my calendar events"
    - "Help"
    """
    
    # Command patterns
    BOOK_PATTERNS = [
        r"book\s+(?:a\s+)?slot",
        r"book\s+(?:a\s+)?session",
        r"i\s+want\s+to\s+book",
        r"schedule\s+(?:a\s+)?session",
        r"\bbook\b",
        r"add\s+.*\b(class|meeting|appointment|event)\b",
    ]
    
    CANCEL_PATTERNS = [
        r"cancel\s+(?:my\s+)?booking",
        r"cancel\s+(?:my\s+)?appointment",
        r"cancel\s+(?:the\s+)?session",
        r"unbook",
    ]
    
    EVENT_PATTERNS = [
        r"show\s+(?:me\s+)?(?:upcoming\s+)?events",
        r"view\s+(?:my\s+)?(?:upcoming\s+)?events",
        r"list\s+events",
        r"what\s+are\s+my\s+events",
    ]
    
    HELP_PATTERNS = [
        r"help",
        r"what\s+can\s+i\s+do",
        r"available\s+commands",
        r"show\s+commands",
    ]
    
    SHARE_PATTERNS = [
        r"share\s+(?:my\s+)?calendar",
        r"how\s+do\s+i\s+share",
        r"calendar\s+sharing",
    ]

    # Ask AI / assistant patterns
    ASK_PATTERNS = [
        r"\bassistant\b",
        r"\bask\s+(?:assistant|ai)\b",
        r"\bhey\s+assistant\b",
        r"\bassistant\b",
    ]

    # Reminder patterns
    REMIND_PATTERNS = [
        r"remind\s+me",
        r"set\s+(?:a\s+)?reminder",
        r"set\s+reminder",
    ]

    # Declarative event patterns (user states they have an event)
    DECLARE_EVENT_PATTERNS = [
        r"\bi have\b",
        r"\bi've got\b",
        r"\bi have a\b",
        r"\bi am going to\b",
        r"\bi'm going to\b",
        r"\bi have an appointment\b",
        r"\bi have a meeting\b",
    ]
    
    CONFIG_PATTERNS = [
        r"config",
        r"configure",
        r"authenticate",
        r"login",
    ]
    
    EXIT_PATTERNS = [
        r"exit",
        r"quit",
        r"goodbye",
        r"bye",
    ]
    
    RESCHEDULE_PATTERNS = [
        r"reschedule",
        r"move\s+my\s+meeting",
        r"change\s+the\s+time",
        r"move\s+the\s+meeting",
    ]
    
    # Find best time patterns (AI scheduling)
    FIND_BEST_TIME_PATTERNS = [
        r"find\s+(?:the\s+)?best\s+time",
        r"find\s+(?:a\s+)?time\s+for",
        r"what\s+time\s+(?:should|can)\s+i\s+(?:have|do)",
        r"when\s+(?:should|can)\s+(?:i|we)\s+(?:meet|do)",
        r"best\s+time\s+for",
        r"find\s+availability",
        r"check\s+(?:my\s+)?availability",
    ]
    
    # Agenda summary patterns
    AGENDA_PATTERNS = [
        r"what's?\s+my\s+day\s+(?:looking\s+)?like",
        r"what\s+do\s+i\s+have\s+(?:today|scheduled)",
        r"what's?\s+on\s+(?:the\s+)?agenda",
        r"summarize\s+(?:my\s+)?(?:day|week|month|schedule)",
        r"give\s+me\s+a\s+(?:day|week|month)\s+summary",
        r"how\s+(?:busy|packed|full)\s+is\s+(?:my\s+)?(?:day|week)",
        r"what's?\s+(?:coming\s+)?up\s+(?:today|this\s+week)",
        r"brief\s+me\s+on\s+(?:today|this\s+week)",
    ]
    
    # AI Pattern & Prediction patterns
    PATTERN_PATTERNS = [
        r"analyze\s+(?:my\s+)?(?:schedule|calendar|patterns)",
        r"(?:what\s+)?patterns?\s+(?:do\s+you\s+see|in\s+my\s+schedule)",
        r"(?:any\s+)?suggestions?\s+(?:for\s+my\s+schedule|to\s+improve)",
        r"predict(?:ions?)?\s+(?:for\s+my\s+(?:week|schedule))?",
        r"(?:detect|find)\s+(?:patterns|opportunities)(?:\s+in\s+my\s+schedule)?",
        r"(?:what\s+)?should\s+i\s+(?:improve|do|change)",
        r"(?:smart\s+)?recommendations?\s+(?:for\s+my\s+schedule)?",
        r"help\s+me\s+(?:optimize|improve|fix)\s+my\s+schedule",
    ]
    
    # Apply prediction/recommendation patterns
    APPLY_PATTERN_PATTERNS = [
        r"(?:apply|use|enable|block)(?:\s+my)?\s+learning\s+(?:time|blocks)",
        r"(?:add|enable)\s+(?:early\s+)?reminders?(?:\s+for\s+early\s+events)?",
        r"(?:add|block)(?:\s+my)?\s+focus\s+time",
        r"(?:add|insert)\s+(?:travel\s+)?buffers?(?:\s+between\s+meetings)?",
        r"(?:schedule|add)\s+breaks?",
        r"(?:apply|use)\s+(?:that|the)\s+suggestion",
        r"go\s+ahead\s+(?:with\s+)?(?:that|the\s+recommendation)",
        r"apply\s+(?:that\s+)?suggestion",
    ]
    
    # Email drafting patterns
    DRAFT_EMAIL_PATTERNS = [
        r"(?:draft|write|send)\s+(?:an?\s+)?email",
        r"(?:draft|write)\s+(?:a\s+)?(?:thank\s+you|thank-you|thanks)",
        r"(?:draft|write)\s+(?:a\s+)?reminder",
        r"(?:draft|write)\s+(?:a\s+)?(?:follow-up|follow\s+up)",
        r"send\s+(?:an?\s+)?email(?:\s+to\s+\w+)?",
        r"compose\s+(?:an?\s+)?email",
    ]
    
    # Voice sentiment/emotion patterns
    SENTIMENT_ANALYSIS_PATTERNS = [
        r"(?:detect|analyze)\s+(?:my\s+)?mood",
        r"(?:how\s+)?(?:do\s+)?(?:i|am\s+i)\s+(?:sound|seem|look)",
        r"(?:what\s+)?emotion.*?(?:detecting|sense|feel)",
        r"stress\s+(?:check|level|analysis)",
        r"(?:am|i'm|i\s+am)\s+(?:stressed|tired|overwhelmed|anxious)",
    ]
    
    # Mood-based calendar adjustment patterns
    MOOD_CALENDAR_PATTERNS = [
        r"(?:if\s+)?(?:i'm|i\s+am|if\s+i'm|if\s+i\s+am)\s+(?:stressed|tired|overwhelmed|anxious).*?(?:shift|move|reduce|lighten|adjust)",
        r"(?:if\s+)?(?:happy|excited).*?(?:add|schedule|plan|suggest).*?(?:fun|break|event)",
        r"(?:shift|move|reduce)\s+(?:my\s+)?meetings.*?(?:i'm|i\s+am).*?(?:stressed|tired)",
        r"(?:lighten|lower)\s+(?:my\s+)?(?:calendar|schedule)\s+(?:load|workload)",
        r"(?:adjust|tweak)\s+(?:my\s+)?calendar\s+(?:to|for).*?(?:mood|stress|energy)",
    ]
    
    # Task extraction patterns
    TASK_EXTRACTION_PATTERNS = [
        r"i\s+(?:must|have\s+to|need\s+to|should)\s+.*?(?:before|by|until)",
        r"(?:extract|find|identify).*?tasks?",
        r"(?:what\s+)?(?:tasks|to\s+dos|todos).*?(?:do\s+)?i\s+have",
        r"remind\s+me\s+to\s+",
        r"i\s+(?:need|have)\s+to\s+.*?(?:today|tomorrow|this\s+week)",
        r"(?:can\s+you\s+)?(?:extract|pull)\s+(?:any\s+)?tasks?\s+from\s+(?:my\s+)?(?:message|text)",
    ]
    
    # Multi-turn conversation patterns
    CONVERSATION_PATTERNS = [
        r"(?:let's\s+)?(?:schedule|plan|arrange|set\s+up)\s+(?:a|an)\s+(?:meeting|session|call)",
        r"(?:help\s+me\s+)?(?:schedule|plan|create).*?(?:meeting|event|task)",
        r"(?:can\s+you\s+)?help\s+me\s+(?:with|arrange)",
        r"(?:let's\s+)?(?:talk\s+about|discuss|go\s+over)\s+(?:my\s+)?(?:calendar|schedule)",
        r"(?:walk\s+me\s+through|step\s+by\s+step)",
        r"(?:let's\s+(?:set\s+)?up|create|make)\s+(?:a\s+)?(?:meeting|event|task)",
        r"(?:i\s+)?(?:want\s+to|need\s+to|like\s+to)\s+(?:schedule|plan|arrange)",
    ]
    
    @staticmethod
    def _match_pattern(text: str, patterns: list) -> bool:
        """Check if text matches any of the given patterns."""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def extract_datetime(text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extracts date and time from voice command text with support for:
        - Absolute dates: "2024-03-01", "03/01/2024", "01-03-2024"
        - Relative dates: "tomorrow", "next Monday", "in 3 days", "next week"
        - Time formats: "10:00", "2:30 pm", "14:30"
        
        Returns:
        Tuple of (date_str, time_str) in formats YYYY-MM-DD and HH:MM
        or (None, None) if not found.
        """
        date_str = None
        time_str = None
        
        # First, try to extract absolute date numeric forms
        date_match = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})', text)
        if date_match:
            date_str = date_match.group(1).replace('/', '-')
        else:
            # Try relative date patterns (today, tomorrow, next friday, etc.)
            relative_date = VoiceCommandParser._parse_relative_date(text)
            if relative_date:
                date_str = relative_date

        # Extract time with prioritized patterns to avoid matching numbers inside years
        # 1) HH:MM with optional AM/PM (e.g., 14:30, 2:30 pm)
        time_match = re.search(r'\b(\d{1,2}):(\d{2})\s*(am|pm)?\b', text, re.IGNORECASE)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            am_pm = time_match.group(3)
            if am_pm:
                am_pm = am_pm.lower()
                if am_pm == 'pm' and hour < 12:
                    hour += 12
                elif am_pm == 'am' and hour == 12:
                    hour = 0
            time_str = f"{hour:02d}:{minute:02d}"
        else:
            # 2) 'at H' or 'at H am/pm' patterns (e.g., at 9, at 9 am, at 12 PM)
            at_time_match = re.search(r'\bat\s+(\d{1,2})(?:\s*(am|pm))?\b', text, re.IGNORECASE)
            if at_time_match:
                hour = int(at_time_match.group(1))
                minute = 0
                am_pm = at_time_match.group(2)
                if am_pm:
                    am_pm = am_pm.lower()
                    if am_pm == 'pm' and hour < 12:
                        hour += 12
                    elif am_pm == 'am' and hour == 12:
                        hour = 0
                time_str = f"{hour:02d}:{minute:02d}"
            else:
                # 3) standalone hour with am/pm (e.g., '9am')
                standalone_am_pm = re.search(r'\b(\d{1,2})\s*(am|pm)\b', text, re.IGNORECASE)
                if standalone_am_pm:
                    hour = int(standalone_am_pm.group(1))
                    minute = 0
                    am_pm = standalone_am_pm.group(2).lower()
                    if am_pm == 'pm' and hour < 12:
                        hour += 12
                    elif am_pm == 'am' and hour == 12:
                        hour = 0
                    time_str = f"{hour:02d}:{minute:02d}"

        # If date or time still missing, try natural language parsing via dateutil (best-effort)
        if DATEUTIL_AVAILABLE and (not date_str or not time_str):
            try:
                dt = du_parser.parse(text, fuzzy=True, default=datetime.now())
                # Only extract date if not already found
                if not date_str:
                    date_str = dt.strftime('%Y-%m-%d')
                if not time_str:
                    time_str = dt.strftime('%H:%M')
            except Exception:
                pass
        
        return date_str, time_str
    
    @staticmethod
    def _parse_relative_date(text: str) -> Optional[str]:
        """
        Parse relative date expressions and convert to YYYY-MM-DD format.
        
        Supports:
        - "today", "tomorrow", "yesterday"
        - "next Monday", "next Friday", etc.
        - "in X days", "in X weeks"
        - Specific day names
        """
        text_lower = text.lower()
        today = datetime.now()
        
        # Handle exact relative dates
        if re.search(r'\btoday\b', text_lower):
            return today.strftime('%Y-%m-%d')
        
        if re.search(r'\btomorrow\b', text_lower):
            return (today + timedelta(days=1)).strftime('%Y-%m-%d')
        
        if re.search(r'\byesterday\b', text_lower):
            return (today - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Handle "next Monday", "next Friday", etc.
        day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day_idx, day_name in enumerate(day_names):
            pattern = rf'\bnext\s+{day_name}\b'
            if re.search(pattern, text_lower):
                # Find next occurrence of that day
                days_ahead = (day_idx - today.weekday()) % 7
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                target_date = today + timedelta(days=days_ahead)
                return target_date.strftime('%Y-%m-%d')
        
        # Handle "in X days" or "in X weeks"
        in_days_match = re.search(r'in\s+(\d+)\s+days?', text_lower)
        if in_days_match:
            days = int(in_days_match.group(1))
            return (today + timedelta(days=days)).strftime('%Y-%m-%d')
        
        in_weeks_match = re.search(r'in\s+(\d+)\s+weeks?', text_lower)
        if in_weeks_match:
            weeks = int(in_weeks_match.group(1))
            return (today + timedelta(weeks=weeks)).strftime('%Y-%m-%d')
        
        # Handle just day names (assume next occurrence)
        for day_idx, day_name in enumerate(day_names):
            if re.search(rf'\b{day_name}\b', text_lower):
                days_ahead = (day_idx - today.weekday()) % 7
                if days_ahead == 0:  # Today is that day
                    days_ahead = 7  # Schedule for next week
                target_date = today + timedelta(days=days_ahead)
                return target_date.strftime('%Y-%m-%d')
        
        return None
    
    @staticmethod
    def extract_summary(text: str) -> Optional[str]:
        """
        Extracts the topic/summary from a booking command.
        Supports: 'for ...', 'about ...', 'and call it ...', 'called ...', or after 'book ... for ...'
        Example: "Book a slot for Python help" → "Python help"
                 "Book a meeting for tomorrow at 3 pm and call it movie date" → "movie date"
        """
        # 1. Look for 'and call it <summary>' or 'called <summary>'
        match = re.search(r'(?:and\s+call\s+it|called)\s+([\w\s\-]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # 2. Look for 'for <summary>'
        match = re.search(r'for\s+(.+?)(?:\s+on|\s+at|$)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # 3. Look for 'about <summary>'
        match = re.search(r'about\s+(.+?)(?:\s+on|\s+at|$)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # 4. Default: extract everything after "book" or similar
        match = re.search(r'book.*?(?:for|studying|topic)?\s+(.+?)$', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return None
    
    @staticmethod
    def parse_command(text: str) -> Tuple[str, dict]:
        """
        Parse voice command text and return command type and parameters.
        
        Returns:
        Tuple of (command_name, parameters_dict)
        
        Command names: 'book', 'cancel-book', 'events', 
                      'help', 'share', 'config', 'exit'
        
        Parameters dict contains parsed details like 'date', 'time', 'summary'
        """
        text_lower = text.lower().strip()
        
        # Check for 'events for the day' or similar
        if VoiceCommandParser._match_pattern(text_lower, VoiceCommandParser.EVENTS_FOR_DAY_PATTERNS):
            # Try to extract a date, default to today if not found
            date_str, _ = VoiceCommandParser.extract_datetime(text)
            if not date_str:
                from datetime import datetime
                date_str = datetime.now().strftime('%Y-%m-%d')
            return 'events-for-day', {'date': date_str}

        # Determine command type
        if VoiceCommandParser._match_pattern(text_lower, VoiceCommandParser.BOOK_PATTERNS):
            date_str, time_str = VoiceCommandParser.extract_datetime(text)
            summary = VoiceCommandParser.extract_summary(text)
            return 'book', {'date': date_str, 'time': time_str, 'summary': summary}
        
        elif VoiceCommandParser._match_pattern(text_lower, VoiceCommandParser.CANCEL_PATTERNS):
            date_str, time_str = VoiceCommandParser.extract_datetime(text)
            return 'cancel-book', {'date': date_str, 'time': time_str}
        
        elif VoiceCommandParser._match_pattern(text_lower, VoiceCommandParser.EVENT_PATTERNS):
            return 'events', {}
        
        elif VoiceCommandParser._match_pattern(text_lower, VoiceCommandParser.HELP_PATTERNS):
            return 'help', {}
        
        elif VoiceCommandParser._match_pattern(text_lower, VoiceCommandParser.SHARE_PATTERNS):
            return 'share', {}

        elif VoiceCommandParser._match_pattern(text_lower, VoiceCommandParser.ASK_PATTERNS):
            # Forward entire text to AI/chat handler
            return 'ai', {'message': text}

        elif VoiceCommandParser._match_pattern(text_lower, VoiceCommandParser.REMIND_PATTERNS):
            # Create a reminder: extract date/time and summary
            date_str, time_str = VoiceCommandParser.extract_datetime(text)
            summary = VoiceCommandParser.extract_summary(text) or 'Reminder'
            return 'set-reminder', {'date': date_str, 'time': time_str, 'summary': summary}

        elif VoiceCommandParser._match_pattern(text_lower, VoiceCommandParser.FIND_BEST_TIME_PATTERNS):
            # Find best time for an event: extract duration and search window
            # e.g., "Find the best time for a 2-hour session sometime next week"
            import re
            duration_match = re.search(r"(\d+)\s*[-\s]*(?:hour|hr|minute|min)\b", text, re.IGNORECASE)
            duration_minutes = 60  # default 1 hour
            if duration_match:
                val = int(duration_match.group(1))
                if re.search(r"hour|hr", duration_match.group(), re.IGNORECASE):
                    duration_minutes = val * 60
                else:
                    duration_minutes = val
            
            # Extract search window (next week = 7 days, etc.)
            search_window_days = 7  # default
            window_match = re.search(r"(?:next\s+)?(\d+)\s+days?|next\s+week|this\s+week", text, re.IGNORECASE)
            if window_match:
                if re.search(r"week", window_match.group(), re.IGNORECASE):
                    search_window_days = 7
                else:
                    search_window_days = int(window_match.group(1))
            
            # Extract event description (what they want to do)
            event_desc = re.sub(r"find\s+(?:the\s+)?best\s+time|for\s+(?:a\s+)?", "", text, flags=re.IGNORECASE).strip()
            event_desc = event_desc or "Meeting"
            
            return 'find-best-time', {
                'event_description': event_desc,
                'duration_minutes': duration_minutes,
                'search_window_days': search_window_days
            }

        elif VoiceCommandParser._match_pattern(text_lower, VoiceCommandParser.AGENDA_PATTERNS):
            # Summarize day or week
            period = 'day'  # default
            if re.search(r"\bweek\b", text_lower):
                period = 'week'
            elif re.search(r"\bmonth\b", text_lower):
                period = 'month'
            
            use_gpt = True  # Use AI enhancement if available
            if re.search(r"brief|quick|short", text_lower):
                use_gpt = False  # Quick summary without GPT
            
            return 'agenda-summary', {
                'period': period,
                'use_gpt': use_gpt
            }

        elif VoiceCommandParser._match_pattern(text_lower, VoiceCommandParser.DECLARE_EVENT_PATTERNS):
            # Declarative statement like "I have a meeting on Friday at 9am"
            date_str, time_str = VoiceCommandParser.extract_datetime(text)
            # Summary: try to extract after "I have" or whole sentence minus date/time
            summary = VoiceCommandParser.extract_summary(text)
            if not summary:
                # Fallback: remove date/time phrases
                summary = re.sub(r"on\s+\w+|\bin\s+\d+\s+days|tomorrow|today|at\s+\d{1,2}:?\d{0,2}\s*(?:am|pm)?","", text, flags=re.IGNORECASE).strip()
            summary = summary or 'Event'
            return 'add-event', {'date': date_str, 'time': time_str, 'summary': summary}

        elif VoiceCommandParser._match_pattern(text_lower, VoiceCommandParser.RESCHEDULE_PATTERNS):
            # Attempt to extract original and target datetimes
            # Look for pattern like: "reschedule my meeting from 2024-03-01 10:00 to 2024-03-02 11:00"
            parts = text.split(' to ')
            orig_date, orig_time = VoiceCommandParser.extract_datetime(parts[0]) if parts else (None, None)
            new_date, new_time = (None, None)
            if len(parts) > 1:
                new_date, new_time = VoiceCommandParser.extract_datetime(parts[1])
            return 'reschedule', {'date': orig_date, 'time': orig_time, 'new_date': new_date, 'new_time': new_time}
        
        elif VoiceCommandParser._match_pattern(text_lower, VoiceCommandParser.PATTERN_PATTERNS):
            # Analyze patterns and get predictions
            return 'predict-patterns', {}
        
        elif VoiceCommandParser._match_pattern(text_lower, VoiceCommandParser.APPLY_PATTERN_PATTERNS):
            # Apply a recommendation from patterns
            # Extract which category if mentioned
            category = None
            if re.search(r"learning", text_lower):
                category = 'learning_blocks'
            elif re.search(r"remind", text_lower):
                category = 'reminder'
            elif re.search(r"focus", text_lower):
                category = 'focus_time'
            elif re.search(r"buffer|travel", text_lower):
                category = 'travel_time'
            elif re.search(r"break", text_lower):
                category = 'break'
            
            return 'apply-prediction', {'category': category}
        
        elif VoiceCommandParser._match_pattern(text_lower, VoiceCommandParser.DRAFT_EMAIL_PATTERNS):
            # Extract email type and recipient
            email_type = 'thank_you'  # default
            recipient = 'Team'
            
            if re.search(r"thank\s+you|thanks", text_lower):
                email_type = 'thank_you'
            elif re.search(r"reminder", text_lower):
                email_type = 'reminder'
            elif re.search(r"follow.*?up", text_lower):
                email_type = 'follow_up'
            elif re.search(r"cancel", text_lower):
                email_type = 'cancellation'
            
            # Try to extract recipient
            recipient_match = re.search(r"(?:to|for)\s+(\w+)", text_lower)
            if recipient_match:
                recipient = recipient_match.group(1).capitalize()
            
            return 'draft-email', {
                'email_type': email_type,
                'recipient': recipient,
                'message': text
            }
        
        elif VoiceCommandParser._match_pattern(text_lower, VoiceCommandParser.SENTIMENT_ANALYSIS_PATTERNS):
            # Analyze emotion/mood
            return 'analyze-sentiment', {
                'text': text
            }
        
        elif VoiceCommandParser._match_pattern(text_lower, VoiceCommandParser.MOOD_CALENDAR_PATTERNS):
            # Adjust calendar based on mood
            return 'mood-calendar-adjust', {
                'text': text
            }
        
        elif VoiceCommandParser._match_pattern(text_lower, VoiceCommandParser.TASK_EXTRACTION_PATTERNS):
            # Extract tasks from conversational text
            return 'extract-tasks', {
                'text': text
            }
        
        elif VoiceCommandParser._match_pattern(text_lower, VoiceCommandParser.CONVERSATION_PATTERNS):
            # Multi-turn conversation (Jarvis-style)
            # Extract conversation type
            conv_type = 'qa'  # default
            if re.search(r"schedule|plan|arrange", text_lower):
                conv_type = 'scheduling'
            elif re.search(r"(?:create|make).*?task", text_lower):
                conv_type = 'task_creation'
            
            # Extract or generate conversation ID
            import uuid
            conversation_id = f"conv_{uuid.uuid4().hex[:8]}"
            
            return 'conversation-turn', {
                'conversation_id': conversation_id,
                'text': text,
                'dialogue_type': conv_type
            }
        
        elif VoiceCommandParser._match_pattern(text_lower, VoiceCommandParser.CONFIG_PATTERNS):
            return 'config', {}
        
        elif VoiceCommandParser._match_pattern(text_lower, VoiceCommandParser.EXIT_PATTERNS):
            return 'exit', {}
        
        else:
            return 'unknown', {}


class VoiceRecognizer:
    """
    Handles speech recognition and microphone input.
    Converts audio to text using Google Speech Recognition API.
    """
    
    def __init__(self, timeout: int = 15, phrase_time_limit: int = 15):
        """
        Initialize the voice recognizer.
        
        Parameters:
        - timeout: How long to wait before stopping listening (seconds). Default: 15 for longer booking commands.
        - phrase_time_limit: Maximum length of a phrase to recognize (seconds). Default: 15 for detailed voice input.
        """
        self.timeout = timeout
        self.phrase_time_limit = phrase_time_limit
        
        if not VOICE_AVAILABLE:
            print("[WARN] speech_recognition not installed.")
            print("   Install with: pip install SpeechRecognition pyaudio")
            self.recognizer = None
            self.microphone = None
        else:
            self.recognizer = sr.Recognizer()
            try:
                self.microphone = sr.Microphone()
            except Exception as e:
                print(f"[WARN] Microphone initialization failed: {e}")
                self.microphone = None
    
    def is_available(self) -> bool:
        """Check if voice recognition is available and working."""
        return VOICE_AVAILABLE and self.recognizer is not None and self.microphone is not None
    
    def listen(self, prompt: str = "Listening for command (speak now)...") -> Optional[str]:
        """
        Listen to microphone input and convert to text.
        
        Parameters:
        - prompt: Message to display to user.
        
        Returns:
        Recognized text (lowercase) or None on failure.
        """
        if not self.is_available():
            print("[ERROR] Voice recognition is not available.")
            return None
        try:
            with self.microphone as source:
                # Adapt to ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print(f"[VOICE] {prompt}")
                # Capture audio
                try:
                    audio = self.recognizer.listen(
                        source,
                        timeout=self.timeout,
                        phrase_time_limit=self.phrase_time_limit
                    )
                except sr.WaitTimeoutError:
                    print("[TIMEOUT] No speech detected (timeout).")
                    return None
            # Recognize speech using Google Speech Recognition
            print("[INFO] Processing audio...")
            text = self.recognizer.recognize_google(audio)
            print(f"[SUCCESS] Heard: \"{text}\"")
            return text.strip().lower()
        except sr.UnknownValueError:
            print("[ERROR] Sorry, could not understand audio. Please try again.")
            return None
        except sr.RequestError as e:
            print(f"[ERROR] Speech recognition failed: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            return None


def get_voice_command() -> Tuple[str, dict]:
    """
    Main voice input pipeline:
    1. Listen to user's voice
    2. Convert speech to text
    3. Parse text to extract command and parameters
    
    Returns:
    Tuple of (command_name, parameters_dict) or ('unknown', {}) on failure.
    """
    recognizer = VoiceRecognizer()
    
    if not recognizer.is_available():
        print("⚠️  Voice input not available. Falling back to text input.")
        return 'unknown', {}
    
    # Listen for voice input
    voice_text = recognizer.listen()
    
    if voice_text is None:
        print("⚠️  Could not get voice input. Please try again or use text input.")
        return 'unknown', {}
    
    # Parse the voice command
    command, params = VoiceCommandParser.parse_command(voice_text)
    
    print(f"📋 Parsed command: {command}")
    if params:
        print(f"   Parameters: {params}")
    
    return command, params


# Global voice output instance
_voice_output = None


def get_voice_output() -> VoiceOutput:
    """
    Get or create the global voice output instance.
    
    Returns:
    VoiceOutput instance for text-to-speech functionality.
    """
    global _voice_output
    if _voice_output is None:
        _voice_output = VoiceOutput()
    return _voice_output


def speak(text: str, wait: bool = True) -> None:
    """
    Convenience function to speak text using the global voice output instance.
    
    Parameters:
    - text: The text to speak.
    - wait: If True, wait for speech to finish before returning.
    """
    voice_output = get_voice_output()
    voice_output.speak(text, wait)


if __name__ == "__main__":
    # Test the voice command functionality
    print("=" * 60)
    print("Voice Command Integration Test")
    print("=" * 60)
    
    print("\n1. Testing VoiceOutput (Text-to-Speech):")
    print("-" * 60)
    
    voice_output = VoiceOutput()
    if voice_output.is_available():
        print("[INFO] Text-to-speech engine initialized.")
        voice_output.speak_response("Welcome to Voice Assistant Calendar. Ready to schedule your events.")
    else:
        print("[WARN] Text-to-speech not available. Install pyttsx3 to enable voice output.")
    
    print("\n2. Testing VoiceCommandParser:")
    print("-" * 60)
    
    # Test command parsing with example texts
    test_commands = [
        "Book a slot on 2024-03-01 at 10:00 for Python help",
        "Cancel my booking on 2024-03-01 at 10:00",
        "Show me upcoming events",
        "Help me with available commands",
    ]
    
    parser = VoiceCommandParser()
    for cmd_text in test_commands:
        command, params = parser.parse_command(cmd_text)
        print(f"\nInput: \"{cmd_text}\"")
        print(f"Command: {command}")
        print(f"Parameters: {params}")
    
    print("\n" + "=" * 60)
    print("3. Testing VoiceRecognizer availability:")
    print("-" * 60)
    
    recognizer = VoiceRecognizer()
    print(f"Voice recognition available: {recognizer.is_available()}")
    
    if recognizer.is_available():
        print("\n[INFO] Uncomment the line below to test live voice input:")
        print("   # voice_text = recognizer.listen()")