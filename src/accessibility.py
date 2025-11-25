"""
AI Accessibility Enhancements for Blind/Low Vision Users

Provides comprehensive accessibility features:
- Intelligent audio-only UI mode with state narration
- Enhanced voice summarization and descriptions
- Voice error correction ("11... wait no, 11:30")
- Adaptive speech rate adjustment
- Screen reader optimization
- Gesture-based voice commands
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


# ============================================================================
# Enums and Data Structures
# ============================================================================

class AccessibilityMode(Enum):
    """Accessibility mode."""
    FULL_SCREEN = "full_screen"           # Normal GUI
    AUDIO_ONLY = "audio_only"             # No visual output
    SCREEN_READER = "screen_reader"       # Max verbosity
    HIGH_CONTRAST = "high_contrast"       # Visual enhancement


class SpeechRate(Enum):
    """Speech rate for text-to-speech."""
    VERY_SLOW = 80          # For complex info
    SLOW = 120              # For learning
    NORMAL = 150            # Standard speed
    FAST = 200              # Quick updates
    VERY_FAST = 250         # Familiar info


class UIElement(Enum):
    """Types of UI elements for screen reader."""
    BUTTON = "button"
    INPUT = "input field"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    LIST_ITEM = "list item"
    LINK = "link"
    DIALOG = "dialog"
    MENU = "menu"


@dataclass
class AccessibilityState:
    """Current accessibility state."""
    mode: AccessibilityMode = AccessibilityMode.FULL_SCREEN
    speech_rate: SpeechRate = SpeechRate.NORMAL
    use_audio_descriptions: bool = True
    verbose_mode: bool = False
    announce_state_changes: bool = True
    enable_error_correction: bool = True
    reading_pace: float = 1.0  # Adaptive reading pace (0.5 - 2.0)
    user_preferences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.user_preferences is None:
            self.user_preferences = {}


# ============================================================================
# Intelligent Audio UI
# ============================================================================

class AudioUIController:
    """
    Manages audio-only interface for blind/low-vision users.
    Provides complete navigation and control via voice and audio feedback.
    """
    
    def __init__(self):
        self.tts_available = TTS_AVAILABLE
        self.engine = None
        self.state = AccessibilityState()
        self.navigation_stack = []  # Track current screen/menu
        self.current_view = "home"  # Current screen being narrated
        
        if self.tts_available:
            try:
                self.engine = pyttsx3.init()
                self._configure_engine()
            except Exception as e:
                print(f"[WARN] TTS initialization failed: {e}")
                self.tts_available = False
    
    def _configure_engine(self):
        """Configure TTS engine."""
        if not self.engine:
            return
        
        self.engine.setProperty('rate', self.state.speech_rate.value)
        self.engine.setProperty('volume', 0.9)
    
    def set_accessibility_mode(self, mode: AccessibilityMode):
        """Switch accessibility mode."""
        self.state.mode = mode
        
        # Announce mode change
        if mode == AccessibilityMode.AUDIO_ONLY:
            self.speak("Switching to audio-only mode. All interaction via voice.")
        elif mode == AccessibilityMode.SCREEN_READER:
            self.speak("Screen reader mode activated. Maximum verbosity enabled.")
        elif mode == AccessibilityMode.HIGH_CONTRAST:
            self.speak("High contrast mode activated for visual users.")
    
    def set_speech_rate(self, rate: SpeechRate):
        """Adjust speech rate."""
        self.state.speech_rate = rate
        if self.engine:
            self.engine.setProperty('rate', rate.value)
        
        self.speak(f"Speech rate set to {rate.name.lower()}.")
    
    def adaptive_speech_rate(self, complexity: float = 0.5):
        """
        Adaptively adjust speech rate based on content complexity.
        
        Args:
            complexity: 0.0 (simple) to 1.0 (complex)
        """
        # Adjust reading pace
        if complexity > 0.8:
            self.state.reading_pace = 0.7  # Slower for complex info
            self.set_speech_rate(SpeechRate.SLOW)
        elif complexity > 0.5:
            self.state.reading_pace = 0.9
            self.set_speech_rate(SpeechRate.NORMAL)
        else:
            self.state.reading_pace = 1.1  # Faster for simple info
            self.set_speech_rate(SpeechRate.FAST)
    
    def speak(self, text: str, wait: bool = True) -> None:
        """Speak text to user."""
        if not self.tts_available or not self.engine:
            print(f"[AUDIO] {text}")
            return
        
        try:
            # Clean up text
            text = text.strip()
            if not text:
                return
            
            self.engine.say(text)
            if wait:
                self.engine.runAndWait()
        except Exception as e:
            print(f"[WARN] TTS error: {e}")
    
    def announce_element(self, element_type: UIElement, label: str, 
                        action_hint: Optional[str] = None):
        """Announce a UI element to screen reader user."""
        announcement = f"{element_type.value}: {label}"
        
        if action_hint:
            announcement += f". {action_hint}"
        
        self.speak(announcement)
    
    def announce_state_change(self, from_state: str, to_state: str):
        """Announce state change (e.g., navigation)."""
        if self.state.announce_state_changes:
            self.speak(f"Moving from {from_state} to {to_state}.")
    
    def navigate_to_screen(self, screen_name: str, content: str):
        """Navigate to new screen with audio description."""
        self.announce_state_change(self.current_view, screen_name)
        self.current_view = screen_name
        self.navigation_stack.append(screen_name)
        
        # Announce screen content
        self.speak(content)
    
    def navigate_back(self):
        """Go back to previous screen."""
        if len(self.navigation_stack) > 1:
            self.navigation_stack.pop()
            prev_screen = self.navigation_stack[-1]
            self.announce_state_change(self.current_view, prev_screen)
            self.current_view = prev_screen
    
    def read_menu(self, menu_items: List[str]):
        """Read menu options aloud."""
        self.speak(f"Menu with {len(menu_items)} options:")
        for i, item in enumerate(menu_items, 1):
            self.speak(f"Option {i}: {item}")
    
    def confirm_action(self, action: str) -> bool:
        """Ask user to confirm an action."""
        self.speak(f"Please confirm: {action}. Say 'yes' or 'no'.")
        # Note: In real implementation, would listen for voice response
        return True
    
    def read_table(self, headers: List[str], rows: List[List[str]]):
        """Read table data aloud."""
        # Read headers
        self.speak(f"Table with {len(headers)} columns: " + ", ".join(headers))
        
        # Read each row
        for row_num, row in enumerate(rows, 1):
            row_text = " ".join([f"{h}: {v}" for h, v in zip(headers, row)])
            self.speak(f"Row {row_num}: {row_text}")


# ============================================================================
# Voice Error Correction
# ============================================================================

class VoiceErrorCorrection:
    """
    Handles voice command corrections and clarifications.
    User: "Book at 11... wait no, 11:30"
    AI: Intelligently updates the time to 11:30
    """
    
    def __init__(self):
        self.last_commands = []  # History of recent commands
        self.pending_correction = None
        self.use_gpt = OPENAI_AVAILABLE
    
    def add_command(self, command: str) -> Dict[str, Any]:
        """Add a command and detect corrections."""
        self.last_commands.append({
            'text': command,
            'timestamp': datetime.now(),
            'processed': False
        })
        
        # Check if this is a correction
        if self._is_correction_signal(command):
            return self._process_correction(command)
        
        return {'command': command, 'is_correction': False}
    
    def _is_correction_signal(self, text: str) -> bool:
        """Detect if user is correcting something."""
        correction_keywords = [
            'wait', 'no', 'actually', 'scratch that', 'i mean',
            'sorry', 'let me rephrase', 'i meant', 'change that',
            'make it', 'instead', 'oops', 'hold on', 'wait no'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in correction_keywords)
    
    def _process_correction(self, correction_text: str) -> Dict[str, Any]:
        """Process a correction command."""
        if not self.last_commands or len(self.last_commands) < 2:
            return {
                'command': correction_text,
                'is_correction': False,
                'message': 'Nothing to correct'
            }
        
        # Get the previous command
        previous = self.last_commands[-2]['text']
        
        # Use GPT to extract what was corrected
        if self.use_gpt:
            return self._process_correction_gpt(previous, correction_text)
        else:
            return self._process_correction_rules(previous, correction_text)
    
    def _process_correction_gpt(self, previous: str, 
                                correction: str) -> Dict[str, Any]:
        """Use GPT to understand the correction."""
        try:
            prompt = f"""User made a correction. Understand the intent:

Original command: "{previous}"
Correction: "{correction}"

What did the user correct? Provide:
1. "original_value": What was being changed from
2. "corrected_value": What it changed to
3. "field": Which field is being corrected (time, duration, date, etc.)
4. "corrected_command": The full corrected command

Return as JSON."""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )
            
            import json
            result = json.loads(response['choices'][0]['message']['content'])
            
            return {
                'command': result.get('corrected_command', previous),
                'is_correction': True,
                'from': result.get('original_value'),
                'to': result.get('corrected_value'),
                'field': result.get('field'),
                'confidence': 0.9
            }
        
        except Exception as e:
            print(f"[WARN] GPT correction failed: {e}")
            return self._process_correction_rules(previous, correction)
    
    def _process_correction_rules(self, previous: str, 
                                  correction: str) -> Dict[str, Any]:
        """Rule-based correction processing."""
        import re
        
        # Extract numbers from both
        prev_numbers = re.findall(r'\d+', previous)
        corr_numbers = re.findall(r'\d+', correction)
        
        # Find what changed
        new_numbers = [n for n in corr_numbers if n not in prev_numbers]
        
        return {
            'command': previous,  # Keep original
            'is_correction': True,
            'from': prev_numbers[0] if prev_numbers else None,
            'to': new_numbers[0] if new_numbers else None,
            'field': 'time' if any(c in correction.lower() for c in ['am', 'pm']) else 'unknown',
            'confidence': 0.6
        }
    
    def get_corrected_command(self) -> Optional[str]:
        """Get the fully corrected command."""
        if self.pending_correction:
            return self.pending_correction.get('command')
        return None


# ============================================================================
# Enhanced Voice Summarization
# ============================================================================

class AccessibleVoiceSummarizer:
    """Generate accessible voice summaries with:
    - Logical flow and pacing
    - Emphasis on important items
    - Clear structure (intro → items → conclusion)
    - Adaptive verbosity
    """
    
    def __init__(self, use_gpt: bool = True):
        self.use_gpt = use_gpt and OPENAI_AVAILABLE
    
    def summarize_agenda(self, events: List[Dict], 
                        verbose: bool = False) -> str:
        """Generate accessible agenda summary."""
        if not events:
            return "You have no events scheduled."
        
        if self.use_gpt and verbose:
            return self._summarize_agenda_gpt(events)
        else:
            return self._summarize_agenda_rules(events, verbose)
    
    def _summarize_agenda_rules(self, events: List[Dict], 
                                verbose: bool = False) -> str:
        """Rule-based agenda summarization."""
        summary = f"You have {len(events)} scheduled events today. "
        
        if verbose:
            summary += "Here are your events: "
            for i, event in enumerate(events, 1):
                title = event.get('title', 'Event')
                start = event.get('start', 'unknown time')
                summary += f"{i}. {title} at {start}. "
        else:
            # Concise version
            first = events[0].get('title', 'First event')
            start = events[0].get('start', 'soon')
            summary += f"Your first event is {first} at {start}."
        
        return summary
    
    def _summarize_agenda_gpt(self, events: List[Dict]) -> str:
        """GPT-powered agenda summarization."""
        try:
            events_text = "\n".join([
                f"- {e.get('title', 'Event')} at {e.get('start', '?')}"
                for e in events
            ])
            
            prompt = f"""Create a brief, accessible voice summary of this calendar 
(for blind/low-vision user). Be natural, conversational, but informative.
Use pauses (indicated by '..') for readability.

Events:
{events_text}

Format: Start with total count, highlight any conflicts or important notes, 
then list events in a conversational way."""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )
            
            return response['choices'][0]['message']['content'].strip()
        
        except Exception as e:
            print(f"[WARN] GPT summarization failed: {e}")
            return self._summarize_agenda_rules(events, verbose=True)
    
    def summarize_event_details(self, event: Dict, 
                               include_participants: bool = True) -> str:
        """Generate detailed accessible event description."""
        title = event.get('title', 'Event')
        start = event.get('start', 'unknown time')
        duration = event.get('duration_minutes', 60)
        description = event.get('description', '')
        participants = event.get('attendees', [])
        
        summary = f"{title}. Starts at {start}, duration {duration} minutes. "
        
        if description:
            summary += f"Description: {description}. "
        
        if include_participants and participants:
            count = len(participants)
            if count == 1:
                summary += f"One participant: {participants[0]}. "
            elif count <= 3:
                summary += f"Participants: {', '.join(participants)}. "
            else:
                summary += f"{count} participants attending. "
        
        return summary


# ============================================================================
# Accessibility Manager
# ============================================================================

class AccessibilityManager:
    """Main accessibility coordinator."""
    
    def __init__(self):
        self.audio_ui = AudioUIController()
        self.error_correction = VoiceErrorCorrection()
        self.summarizer = AccessibleVoiceSummarizer(use_gpt=True)
    
    def enable_audio_only_mode(self):
        """Enable audio-only interface."""
        self.audio_ui.set_accessibility_mode(AccessibilityMode.AUDIO_ONLY)
    
    def enable_screen_reader_mode(self):
        """Enable screen reader mode."""
        self.audio_ui.set_accessibility_mode(AccessibilityMode.SCREEN_READER)
    
    def set_speech_rate(self, rate: SpeechRate):
        """Set speech rate."""
        self.audio_ui.set_speech_rate(rate)
    
    def process_voice_command(self, command: str) -> Dict[str, Any]:
        """Process voice command with error correction."""
        correction_result = self.error_correction.add_command(command)
        
        if correction_result.get('is_correction'):
            # Announce the correction
            from_val = correction_result.get('from')
            to_val = correction_result.get('to')
            self.audio_ui.speak(
                f"Understood. Changed {correction_result.get('field')} "
                f"from {from_val} to {to_val}."
            )
            confidence = correction_result.get('confidence', 0.8)
            if confidence < 0.7:
                self.audio_ui.speak("Please confirm this change.")
        
        return correction_result
    
    def read_agenda(self, events: List[Dict], verbose: bool = False):
        """Read calendar agenda."""
        summary = self.summarizer.summarize_agenda(events, verbose=verbose)
        self.audio_ui.speak(summary)
    
    def describe_event(self, event: Dict):
        """Read detailed event description."""
        summary = self.summarizer.summarize_event_details(event)
        self.audio_ui.speak(summary)
    
    def announce_state(self, state_info: str):
        """Announce current system state."""
        self.audio_ui.speak(f"Current state: {state_info}")


# ============================================================================
# Quick Helpers
# ============================================================================

def create_accessible_manager() -> AccessibilityManager:
    """Factory to create accessibility manager."""
    return AccessibilityManager()


def enable_blind_user_mode():
    """Quick setup for blind/low-vision users."""
    manager = AccessibilityManager()
    manager.enable_audio_only_mode()
    manager.set_speech_rate(SpeechRate.NORMAL)
    manager.audio_ui.speak(
        "Accessibility mode enabled for blind and low-vision users. "
        "You can navigate using voice commands. Say 'help' for available commands."
    )
    return manager
