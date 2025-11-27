"""
Voice Pipeline Orchestrator - Complete voice interaction flow
Coordinates: Wake Word → Recording → Cleanup → STT → NLU → Action → TTS → Playback
"""

import logging
import time
from typing import Dict, Optional, Callable

from src.wakeword.wake_engine import get_wake_engine
from src.stt.speech_engine import get_stt_engine
from src.audio_processing.cleanup import get_audio_cleanup
from src.ai.voice_parser import parse_transcript
from src.actions.calendar_actions import create_event, get_events, cancel_event
from src.tts.tts_engine import get_tts_engine

logger = logging.getLogger(__name__)


class VoicePipeline:
    """Orchestrate complete voice interaction flow"""
    
    def __init__(self):
        self.wake_engine = get_wake_engine()
        self.stt_engine = get_stt_engine()
        self.audio_cleanup = get_audio_cleanup()
        self.tts_engine = get_tts_engine()
        
        self.state = "IDLE"  # IDLE, TRIGGER_DETECTED, CAPTURING, PROCESSING, RESPONDING
        self.current_user_id = None
        self.audio_buffer = bytearray()
        self.silence_count = 0
        self.max_silence_frames = 24  # 1.5s @ 16kHz, 4096 chunk size
    
    def process_audio_chunk(
        self,
        audio_chunk: bytes,
        user_id: str,
        is_final: bool = False
    ) -> Dict:
        """
        Main pipeline entry point - process audio chunk
        
        Args:
            audio_chunk: Raw PCM audio (16-bit, 16kHz)
            user_id: User identifier
            is_final: True if this is the final chunk
        
        Returns:
            {
                "state": str,
                "action": str or None,
                "transcript": str or None,
                "assistant_text": str or None,
                "audio_path": str or None,
                "needs_more_info": bool,
                "error": str or None
            }
        """
        self.current_user_id = user_id
        
        try:
            # Stage 1: Check for wake word (if in IDLE)
            if self.state == "IDLE":
                return self._handle_idle_state(audio_chunk, user_id)
            
            # Stage 4: Collect audio (if in CAPTURING)
            elif self.state == "CAPTURING":
                return self._handle_capturing_state(audio_chunk, user_id, is_final)
            
            # Unknown state
            else:
                logger.error(f"Unknown state: {self.state}")
                return {
                    "state": self.state,
                    "error": "Unknown pipeline state"
                }
        
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            self.state = "IDLE"
            return {
                "state": "IDLE",
                "error": str(e)
            }
    
    def _handle_idle_state(self, audio_chunk: bytes, user_id: str) -> Dict:
        """Stage 1-2: Check for wake word activation"""
        try:
            # Check for wake word
            result = self.wake_engine.detect_wake_word(audio_chunk)
            
            if result["detected"] and result["confidence"] > 0.5:
                # Wake word detected!
                logger.info(f"Wake word detected (confidence: {result['confidence']})")
                
                # Transition to TRIGGER_DETECTED
                self.state = "TRIGGER_DETECTED"
                self.audio_buffer = bytearray()
                self.silence_count = 0
                
                # Return activation feedback
                return {
                    "state": "TRIGGER_DETECTED",
                    "action": "activate",
                    "message": "Listening for your command...",
                    "play_beep": True
                }
            
            else:
                # No wake word detected, stay idle
                return {
                    "state": "IDLE",
                    "action": None
                }
        
        except Exception as e:
            logger.error(f"Wake word detection failed: {e}")
            return {
                "state": "IDLE",
                "error": str(e)
            }
    
    def _handle_capturing_state(
        self,
        audio_chunk: bytes,
        user_id: str,
        is_final: bool
    ) -> Dict:
        """Stage 4-5: Capture and process audio"""
        try:
            # Add to buffer
            self.audio_buffer.extend(audio_chunk)
            
            # Check for silence
            silence_result = self.stt_engine.detect_silence(audio_chunk)
            
            if silence_result["is_silent"]:
                self.silence_count += 1
            else:
                self.silence_count = 0  # Reset silence counter
            
            # Check for silence timeout or final chunk
            if is_final or self.silence_count >= self.max_silence_frames:
                logger.info("Silence detected or final chunk, processing audio")
                
                # Stage 5: Stop recording
                self.state = "PROCESSING"
                
                # Stage 6: Audio cleanup
                return self._process_audio(user_id)
            
            else:
                # Still recording
                return {
                    "state": "CAPTURING",
                    "action": "recording",
                    "buffer_size": len(self.audio_buffer)
                }
        
        except Exception as e:
            logger.error(f"Audio capture failed: {e}")
            self.state = "IDLE"
            return {
                "state": "IDLE",
                "error": str(e)
            }
    
    def _process_audio(self, user_id: str) -> Dict:
        """Stage 6-7: Cleanup and STT recognition"""
        try:
            audio_bytes = bytes(self.audio_buffer)
            
            # Stage 6: Audio cleanup
            logger.info("Running audio cleanup pipeline...")
            cleanup_result = self.audio_cleanup.cleanup_audio(audio_bytes)
            
            if cleanup_result["success"]:
                audio_cleaned = cleanup_result["audio_cleaned"]
            else:
                logger.warning("Audio cleanup failed, using raw audio")
                audio_cleaned = audio_bytes
            
            # Stage 7: Speech recognition
            logger.info("Running speech recognition...")
            stt_result = self.stt_engine.recognize_speech(audio_cleaned)
            
            transcript = stt_result.get("result", "")
            confidence = stt_result.get("confidence", 0)
            
            # Check confidence
            if confidence < 0.60 and transcript and transcript != "no speech detected":
                # Low confidence, ask for repeat
                logger.warning(f"Low STT confidence: {confidence}")
                self.state = "IDLE"
                return {
                    "state": "IDLE",
                    "action": "repeat",
                    "assistant_text": "I didn't catch that clearly. Could you please repeat?",
                    "spoken_time": None,
                    "needs_more_info": True
                }
            
            if not transcript or stt_result.get("is_silent"):
                # No speech detected
                logger.warning("No speech detected")
                self.state = "IDLE"
                return {
                    "state": "IDLE",
                    "action": "no_speech",
                    "assistant_text": "I didn't hear anything. Please try again.",
                    "spoken_time": None,
                    "needs_more_info": False
                }
            
            # Stage 8: NLU processing
            logger.info(f"Parsing transcript: {transcript}")
            return self._parse_and_execute(user_id, transcript)
        
        except Exception as e:
            logger.error(f"Audio processing failed: {e}")
            self.state = "IDLE"
            return {
                "state": "IDLE",
                "error": str(e)
            }
    
    def _parse_and_execute(self, user_id: str, transcript: str) -> Dict:
        """Stage 8-9: Parse intent and execute action"""
        try:
            # Stage 8: NLU parsing
            nlu_result = parse_transcript(transcript)
            
            if not nlu_result.get("ok"):
                # Parsing failed
                self.state = "IDLE"
                return {
                    "state": "IDLE",
                    "action": "parse_error",
                    "assistant_text": "I didn't understand that. Can you rephrase?",
                    "spoken_time": None,
                    "needs_more_info": True
                }
            
            action = nlu_result.get("action")
            
            # Stage 9: Execute action
            logger.info(f"Executing action: {action}")
            action_result = self._execute_action(user_id, action, nlu_result)
            
            # Stage 10: TTS synthesis
            self.state = "RESPONDING"
            return self._synthesize_response(action_result)
        
        except Exception as e:
            logger.error(f"Parse and execute failed: {e}")
            self.state = "IDLE"
            return {
                "state": "IDLE",
                "error": str(e)
            }
    
    def _execute_action(self, user_id: str, action: str, nlu_result: Dict) -> Dict:
        """Execute calendar action"""
        try:
            if action == "create_event":
                result = create_event(
                    user_id=user_id,
                    title=nlu_result.get("title", "Untitled"),
                    date_str=nlu_result.get("date", "today"),
                    time_str=nlu_result.get("time", "12:00"),
                    timezone="America/New_York"
                )
                
                if result.get("success"):
                    return {
                        "success": True,
                        "action": "create_event",
                        "assistant_text": f"I've scheduled {result['event']['title']} for {nlu_result.get('date', 'today')} at {nlu_result.get('spoken_time', 'the scheduled time')}",
                        "spoken_time": nlu_result.get("spoken_time"),
                        "needs_more_info": False
                    }
                else:
                    return {
                        "success": False,
                        "action": "create_event",
                        "assistant_text": "I couldn't create that event. Please try again.",
                        "error": result.get("error")
                    }
            
            elif action == "get_events":
                result = get_events(
                    user_id=user_id,
                    date_str=nlu_result.get("date", "today"),
                    timezone="America/New_York"
                )
                
                if result.get("success"):
                    events = result.get("events", [])
                    if events:
                        event_list = "; ".join([
                            f"{e['title']} at {e.get('spoken_time', 'TBD')}"
                            for e in events
                        ])
                        assistant_text = f"You have {len(events)} event(s): {event_list}"
                    else:
                        assistant_text = f"You have no events scheduled for {nlu_result.get('date', 'today')}"
                    
                    return {
                        "success": True,
                        "action": "get_events",
                        "assistant_text": assistant_text,
                        "spoken_time": None,
                        "needs_more_info": False,
                        "events": events
                    }
                else:
                    return {
                        "success": False,
                        "action": "get_events",
                        "assistant_text": "I couldn't access your calendar.",
                        "error": result.get("error")
                    }
            
            elif action == "cancel_event":
                event_id = nlu_result.get("event_id")
                if not event_id:
                    return {
                        "success": False,
                        "assistant_text": "Which event would you like to cancel?",
                        "spoken_time": None,
                        "needs_more_info": True
                    }
                
                result = cancel_event(user_id=user_id, event_id=event_id)
                
                if result.get("success"):
                    return {
                        "success": True,
                        "action": "cancel_event",
                        "assistant_text": f"I've cancelled that event.",
                        "spoken_time": None,
                        "needs_more_info": False
                    }
                else:
                    return {
                        "success": False,
                        "assistant_text": "I couldn't cancel that event.",
                        "error": result.get("error")
                    }
            
            else:
                # Unknown action
                return {
                    "success": False,
                    "assistant_text": "I didn't understand that command.",
                    "spoken_time": None,
                    "needs_more_info": True
                }
        
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return {
                "success": False,
                "assistant_text": "Something went wrong. Please try again.",
                "error": str(e)
            }
    
    def _synthesize_response(self, action_result: Dict) -> Dict:
        """Stage 10: Synthesize TTS audio"""
        try:
            assistant_text = action_result.get("assistant_text", "")
            spoken_time = action_result.get("spoken_time")
            
            # Synthesize audio
            tts_result = self.tts_engine.synthesize_text(
                text=assistant_text,
                voice="female",
                speed="normal"
            )
            
            if tts_result["success"]:
                # Stage 11: Playback (handled by frontend)
                self.state = "IDLE"
                
                return {
                    "state": "IDLE",
                    "action": action_result.get("action"),
                    "transcript": action_result.get("transcript"),
                    "assistant_text": assistant_text,
                    "spoken_time": spoken_time,
                    "audio_path": tts_result["audio_path"],
                    "duration_ms": tts_result["duration_ms"],
                    "needs_more_info": action_result.get("needs_more_info", False),
                    "events": action_result.get("events")
                }
            else:
                # TTS failed, return text only
                self.state = "IDLE"
                return {
                    "state": "IDLE",
                    "action": action_result.get("action"),
                    "assistant_text": assistant_text,
                    "spoken_time": spoken_time,
                    "audio_path": None,
                    "needs_more_info": action_result.get("needs_more_info", False),
                    "fallback": "text_only",
                    "error": tts_result.get("error")
                }
        
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            self.state = "IDLE"
            return {
                "state": "IDLE",
                "error": str(e)
            }
    
    def reset(self):
        """Reset pipeline to idle"""
        self.state = "IDLE"
        self.audio_buffer = bytearray()
        self.silence_count = 0
        logger.info("Pipeline reset to IDLE")


# Global instance
pipeline = None

def get_pipeline() -> VoicePipeline:
    """Get or create voice pipeline instance"""
    global pipeline
    if pipeline is None:
        pipeline = VoicePipeline()
    return pipeline
