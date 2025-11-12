"""
Voice Command Integration Module

This module handles voice input, speech recognition, and command parsing.
It converts spoken commands into executable actions for the Code Clinics calendar system.
"""

import re
from typing import Optional, Tuple

try:
    import speech_recognition as sr
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False


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
        Extracts date and time from voice command text.
        
        Returns:
        Tuple of (date_str, time_str) in formats YYYY-MM-DD and HH:MM
        or (None, None) if not found.
        """
        date_match = re.search(
            r'(\d{4}[-/]\d{2}[-/]\d{2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            text
        )
        
        time_match = re.search(r'(\d{1,2}):(\d{2})\s*(?:am|pm)?', text, re.IGNORECASE)
        
        date_str = None
        time_str = None
        
        if date_match:
            date_str = date_match.group(1).replace('/', '-')
        
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            
            # Check for AM/PM
            am_pm_match = re.search(r'(am|pm)', text, re.IGNORECASE)
            if am_pm_match:
                am_pm = am_pm_match.group(1).lower()
                if am_pm == 'pm' and hour < 12:
                    hour += 12
                elif am_pm == 'am' and hour == 12:
                    hour = 0
            
            time_str = f"{hour:02d}:{minute:02d}"
        
        return date_str, time_str
    
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
            print("⚠️  Warning: speech_recognition not installed.")
            print("   Install with: pip install SpeechRecognition pyaudio")
            self.recognizer = None
            self.microphone = None
        else:
            self.recognizer = sr.Recognizer()
            try:
                self.microphone = sr.Microphone()
            except Exception as e:
                print(f"⚠️  Microphone initialization failed: {e}")
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
            print("❌ Voice recognition is not available.")
            return None
        
        try:
            with self.microphone as source:
                # Adapt to ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print(f"🎤 {prompt}")
                
                # Capture audio
                try:
                    audio = self.recognizer.listen(
                        source,
                        timeout=self.timeout,
                        phrase_time_limit=self.phrase_time_limit
                    )
                except sr.WaitTimeoutError:
                    print("⏱️  No speech detected (timeout).")
                    return None
            
            # Recognize speech using Google Speech Recognition
            print("⏳ Processing audio...")
            text = self.recognizer.recognize_google(audio)
            print(f"✅ Heard: \"{text}\"")
            return text.strip().lower()
        
        except sr.UnknownValueError:
            print("❌ Sorry, could not understand audio. Please try again.")
            return None
        
        except sr.RequestError as e:
            print(f"❌ Speech recognition failed: {e}")
            return None
        
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
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


if __name__ == "__main__":
    # Test the voice command functionality
    print("=" * 60)
    print("Voice Command Integration Test")
    print("=" * 60)
    
    print("\n1. Testing VoiceCommandParser:")
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
    print("2. Testing VoiceRecognizer availability:")
    print("-" * 60)
    
    recognizer = VoiceRecognizer()
    print(f"Voice recognition available: {recognizer.is_available()}")
    
    if recognizer.is_available():
        print("\n⚠️  Uncomment the line below to test live voice input:")
        print("   # voice_text = recognizer.listen()")
