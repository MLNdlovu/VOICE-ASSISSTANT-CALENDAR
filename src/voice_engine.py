"""
Advanced Voice Engine for Voice Assistant Calendar
Handles speech recognition, text-to-speech, trigger detection, and conversation management
"""

import speech_recognition as sr
import pyttsx3
import threading
import time
from typing import Optional, Callable, Dict, Any, List
from queue import Queue
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class VoiceState:
    """State of the voice assistant"""
    is_listening: bool = False
    is_speaking: bool = False
    user_trigger: str = "XX00"
    user_name: str = "User"
    is_active: bool = False
    last_recognized_text: str = ""
    last_error: str = ""
    conversation_context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.conversation_context is None:
            self.conversation_context = {}


class VoiceEngine:
    """
    Advanced voice engine for handling:
    - Speech recognition (STT)
    - Text-to-speech (TTS)
    - Trigger phrase detection
    - Voice command processing
    - Conversation management
    """
    
    def __init__(self, user_trigger: str = "XX00", user_name: str = "User"):
        self.state = VoiceState(user_trigger=user_trigger.upper(), user_name=user_name)
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
        
        # Initialize TTS
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 150)
        self.tts_engine.setProperty('volume', 0.9)
        
        # Command callback
        self.on_command_recognized: Optional[Callable] = None
        self.on_state_changed: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        # Voice threads
        self._listening_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
    def speak(self, text: str, wait: bool = True) -> None:
        """
        Speak text using TTS
        
        Args:
            text: Text to speak
            wait: Wait for speech to finish before returning
        """
        try:
            self.state.is_speaking = True
            self._notify_state_change()
            
            self.tts_engine.say(text)
            if wait:
                self.tts_engine.runAndWait()
            else:
                # Run in background thread
                thread = threading.Thread(target=self.tts_engine.runAndWait, daemon=True)
                thread.start()
            
            self.state.is_speaking = False
            self._notify_state_change()
        except Exception as e:
            self._handle_error(f"TTS Error: {str(e)}")
    
    def listen(self, timeout: int = 10) -> Optional[str]:
        """
        Listen for voice input and return recognized text
        
        Args:
            timeout: Maximum seconds to listen
            
        Returns:
            Recognized text or None if timeout/error
        """
        try:
            self.state.is_listening = True
            self._notify_state_change()
            
            with sr.Microphone() as source:
                print(f"🎤 Listening for {timeout} seconds...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            
            self.state.is_listening = False
            self._notify_state_change()
            
            # Try Google Speech Recognition first, fallback to other services
            try:
                text = self.recognizer.recognize_google(audio)
                self.state.last_recognized_text = text
                print(f"✓ Recognized: {text}")
                return text
            except sr.UnknownValueError:
                self._handle_error("Could not understand audio")
                return None
            except sr.RequestError as e:
                self._handle_error(f"Speech recognition service error: {str(e)}")
                return None
                
        except sr.RequestError as e:
            self._handle_error(f"Microphone error: {str(e)}")
            return None
        except Exception as e:
            self._handle_error(f"Listen error: {str(e)}")
            return None
    
    def detect_trigger(self, text: str) -> bool:
        """
        Detect if text contains user's trigger phrase
        
        Args:
            text: Text to check
            
        Returns:
            True if trigger detected
        """
        # Normalize text
        normalized = text.upper().replace(" ", "").replace("-", "")
        trigger = self.state.user_trigger.upper().replace(" ", "").replace("-", "")
        
        # Check exact match or with some typo tolerance
        if trigger in normalized:
            return True
        
        # Check with phonetic variations (common voice recognition errors)
        # E.g., "two" for "2", "oh" for "0"
        variations = normalized
        variations = variations.replace("ZERO", "0").replace("OH", "0")
        variations = variations.replace("ONE", "1").replace("WON", "1")
        variations = variations.replace("TWO", "2").replace("TOO", "2")
        variations = variations.replace("THREE", "3").replace("TREE", "3")
        variations = variations.replace("FOUR", "4").replace("FOR", "4")
        variations = variations.replace("FIVE", "5")
        variations = variations.replace("SIX", "6")
        variations = variations.replace("SEVEN", "7")
        variations = variations.replace("EIGHT", "8")
        variations = variations.replace("NINE", "9")
        variations = variations.replace("TEN", "10")
        
        return trigger in variations
    
    def wait_for_trigger(self, max_attempts: int = 5) -> bool:
        """
        Listen for user's trigger phrase
        
        Args:
            max_attempts: Maximum listen attempts before giving up
            
        Returns:
            True if trigger detected
        """
        self.speak(f"Hi {self.state.user_name}! Say your trigger: {self.state.user_trigger}")
        
        for attempt in range(max_attempts):
            text = self.listen(timeout=5)
            
            if text and self.detect_trigger(text):
                print(f"✓ Trigger detected!")
                self.speak("What can I do for you today?")
                return True
            else:
                remaining = max_attempts - attempt - 1
                if remaining > 0:
                    self.speak(f"I didn't catch that. Please try again. {remaining} attempts remaining.")
                else:
                    self.speak("Sorry, I didn't detect your trigger. Please try again later.")
        
        return False
    
    def start_active_listening(self) -> None:
        """Start continuous voice listening in background thread"""
        if self.state.is_active:
            return
        
        self.state.is_active = True
        self._stop_event.clear()
        self._listening_thread = threading.Thread(target=self._listening_loop, daemon=True)
        self._listening_thread.start()
        self.speak(f"Hello {self.state.user_name}! I'm ready. Say your trigger '{self.state.user_trigger}' to wake me up.")
    
    def stop_active_listening(self) -> None:
        """Stop continuous voice listening"""
        self.state.is_active = False
        self._stop_event.set()
        self.speak("Deactivating voice assistant. Goodbye!")
    
    def _listening_loop(self) -> None:
        """Main listening loop running in background thread"""
        while self.state.is_active and not self._stop_event.is_set():
            try:
                text = self.listen(timeout=5)
                
                if not text:
                    continue
                
                # Check for stop commands
                if any(cmd in text.lower() for cmd in ["stop listening", "deactivate", "go to sleep"]):
                    self.stop_active_listening()
                    break
                
                # Check for trigger
                if self.detect_trigger(text):
                    self.speak("Yes, what can I do for you?")
                    # Wait for actual command
                    command = self.listen(timeout=10)
                    if command:
                        if self.on_command_recognized:
                            self.on_command_recognized(command)
                
            except Exception as e:
                print(f"Listening loop error: {e}")
                time.sleep(1)
    
    def _notify_state_change(self) -> None:
        """Notify listeners of state change"""
        if self.on_state_changed:
            try:
                self.on_state_changed(self.state)
            except Exception as e:
                print(f"State change notification error: {e}")
    
    def _handle_error(self, error_msg: str) -> None:
        """Handle errors"""
        self.state.last_error = error_msg
        print(f"❌ {error_msg}")
        if self.on_error:
            try:
                self.on_error(error_msg)
            except Exception as e:
                print(f"Error handler error: {e}")
    
    def set_user_info(self, user_trigger: str, user_name: str) -> None:
        """Update user trigger and name"""
        self.state.user_trigger = user_trigger.upper()
        self.state.user_name = user_name
    
    def get_state_json(self) -> str:
        """Get current state as JSON"""
        return json.dumps({
            'is_listening': self.state.is_listening,
            'is_speaking': self.state.is_speaking,
            'user_trigger': self.state.user_trigger,
            'user_name': self.state.user_name,
            'is_active': self.state.is_active,
            'last_recognized_text': self.state.last_recognized_text,
            'last_error': self.state.last_error,
        })
    
    def __del__(self):
        """Cleanup on object destruction"""
        try:
            self.stop_active_listening()
        except:
            pass


# Global voice engine instance
_voice_engine: Optional[VoiceEngine] = None


def get_voice_engine(user_trigger: str = "XX00", user_name: str = "User") -> VoiceEngine:
    """Get or create global voice engine instance"""
    global _voice_engine
    if _voice_engine is None:
        _voice_engine = VoiceEngine(user_trigger, user_name)
    return _voice_engine


def reset_voice_engine() -> None:
    """Reset global voice engine instance"""
    global _voice_engine
    if _voice_engine:
        _voice_engine.stop_active_listening()
    _voice_engine = None
