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
    """
    Parses natural language voice commands and extracts relevant parameters.
    
    Supports commands like:
    - "Book a slot on 2024-03-01 at 10:00 for Python help"
    - "Cancel my booking on 2024-03-01 at 10:00"
    - "Show me upcoming events"
    - "Show code clinics calendar"
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
    
    CODE_CLINICS_PATTERNS = [
        r"show\s+(?:me\s+)?code\s+clinics",
        r"view\s+code\s+clinics",
        r"code\s+clinic\s+(?:calendar|events|schedule)",
        r"list\s+code\s+clinic\s+slots",
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
        
        Example: "Book a slot for Python help" → "Python help"
        """
        # Look for "for", "about", "on", "studying", etc.
        patterns = [
            r'(?:for|about|studying|help\s+with|learn)\s+(.+?)(?:\s+on\s+|\s+at\s+|$)',
            r'(?:study|help|topic|subject)\s+(?:is|:)?\s*(.+?)(?:\s+on\s+|\s+at\s+|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Default: extract everything after "book" or similar
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
        
        Command names: 'book', 'cancel-book', 'events', 'code-clinics', 
                      'help', 'share', 'config', 'exit'
        
        Parameters dict contains parsed details like 'date', 'time', 'summary'
        """
        text_lower = text.lower().strip()
        
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
        
        elif VoiceCommandParser._match_pattern(text_lower, VoiceCommandParser.CODE_CLINICS_PATTERNS):
            return 'code-clinics', {}
        
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
    
    def __init__(self, timeout: int = 5, phrase_time_limit: int = 6):
        """
        Initialize the voice recognizer.
        
        Parameters:
        - timeout: How long to wait before stopping listening (seconds).
        - phrase_time_limit: Maximum length of a phrase to recognize (seconds).
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
        "Show code clinics calendar",
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
