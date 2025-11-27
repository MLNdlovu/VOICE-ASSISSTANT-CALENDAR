"""
TTS Engine Module - Text-to-Speech Synthesis
Supports Coqui TTS (primary) and gTTS (fallback)
"""

import os
import json
import time
import tempfile
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

try:
    from TTS.api import TTS
    COQUI_AVAILABLE = True
except ImportError:
    COQUI_AVAILABLE = False
    TTS = None

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    gTTS = None

logger = logging.getLogger(__name__)

# Configuration
TTS_CONFIG = {
    "default_voice": "female",
    "default_speed": "normal",
    "coqui_model": "tts_models/en/ljspeech/glow-tts",
    "coqui_vocoder": "vocoder_models/en/ljspeech/univnet",
    "sample_rate": 22050,
    "temp_dir": "/tmp/tts",
    "cache_enabled": True,
    "cache_max_size_mb": 100
}

# Voice profiles
VOICE_PROFILES = {
    "female": {
        "pitch": 1.2,
        "rate": 0.9,
        "name": "Sarah"
    },
    "male": {
        "pitch": 0.8,
        "rate": 0.95,
        "name": "David"
    }
}

# Speed multipliers
SPEED_MULTIPLIERS = {
    "slow": 0.8,
    "normal": 1.0,
    "fast": 1.2
}


class TTSEngine:
    """Text-to-Speech synthesis engine with fallback support"""
    
    def __init__(self):
        self.coqui_model = None
        self.cache = {}
        self.ensure_temp_dir()
        self.initialize_engines()
    
    def ensure_temp_dir(self):
        """Create temp directory for audio files"""
        os.makedirs(TTS_CONFIG["temp_dir"], exist_ok=True)
    
    def initialize_engines(self):
        """Initialize available TTS engines"""
        if COQUI_AVAILABLE:
            try:
                logger.info("Loading Coqui TTS model...")
                self.coqui_model = TTS(
                    model_name=TTS_CONFIG["coqui_model"],
                    vocoder_name=TTS_CONFIG["coqui_vocoder"],
                    gpu=False
                )
                logger.info("✓ Coqui TTS loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Coqui TTS: {e}")
                self.coqui_model = None
        else:
            logger.warning("Coqui TTS not installed")
        
        if GTTS_AVAILABLE:
            logger.info("✓ gTTS available as fallback")
        else:
            logger.warning("gTTS not installed")
    
    def synthesize_text(
        self,
        text: str,
        voice: str = "female",
        speed: str = "normal"
    ) -> Dict:
        """
        Synthesize text to speech
        
        Args:
            text: Assistant response text
            voice: "female" or "male"
            speed: "slow", "normal", or "fast"
        
        Returns:
            {
                "success": bool,
                "audio_path": str or None,
                "duration_ms": int,
                "engine": "coqui" | "gtts" | "error",
                "error": str or None
            }
        """
        # Validate input
        text = self._sanitize_text(text)
        if not text:
            return {
                "success": False,
                "audio_path": None,
                "duration_ms": 0,
                "engine": "error",
                "error": "Empty text"
            }
        
        # Check cache
        cache_key = f"{text}_{voice}_{speed}"
        if TTS_CONFIG["cache_enabled"] and cache_key in self.cache:
            logger.info(f"TTS cache hit for: {text[:30]}...")
            return self.cache[cache_key]
        
        # Try Coqui first
        if self.coqui_model:
            result = self._synthesize_coqui(text, voice, speed)
            if result["success"]:
                self._cache_result(cache_key, result)
                return result
        
        # Fall back to gTTS
        if GTTS_AVAILABLE:
            result = self._synthesize_gtts(text, voice, speed)
            if result["success"]:
                self._cache_result(cache_key, result)
                return result
        
        # All engines failed
        return {
            "success": False,
            "audio_path": None,
            "duration_ms": 0,
            "engine": "error",
            "error": "All TTS engines unavailable"
        }
    
    def synthesize_with_timing(
        self,
        text: str,
        spoken_time: str,
        voice: str = "female",
        speed: str = "normal"
    ) -> Dict:
        """
        Synthesize with emphasis on spoken time
        
        Args:
            text: Main response
            spoken_time: Time phrase (e.g., "2 PM")
            voice: Voice choice
            speed: Speed setting
        
        Returns: Same as synthesize_text()
        """
        # Insert pause before time
        enhanced_text = text.replace(spoken_time, f" [pause] {spoken_time}")
        
        return self.synthesize_text(enhanced_text, voice, speed)
    
    def _synthesize_coqui(self, text: str, voice: str, speed: str) -> Dict:
        """Use Coqui TTS for synthesis"""
        try:
            if not self.coqui_model:
                return {"success": False, "error": "Coqui model not loaded"}
            
            start_time = time.time()
            
            # Synthesize
            output_path = os.path.join(
                TTS_CONFIG["temp_dir"],
                f"tts_{int(time.time()*1000)}.wav"
            )
            
            self.coqui_model.tts_to_file(
                text=text,
                file_path=output_path,
                speaker=voice,
                language="en"
            )
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Apply speed adjustment
            speed_multiplier = SPEED_MULTIPLIERS.get(speed, 1.0)
            adjusted_duration = int(duration_ms / speed_multiplier)
            
            logger.info(f"Coqui synthesis successful: {adjusted_duration}ms")
            
            return {
                "success": True,
                "audio_path": output_path,
                "duration_ms": adjusted_duration,
                "engine": "coqui",
                "error": None
            }
        
        except Exception as e:
            logger.error(f"Coqui TTS failed: {e}")
            return {
                "success": False,
                "audio_path": None,
                "duration_ms": 0,
                "engine": "coqui",
                "error": str(e)
            }
    
    def _synthesize_gtts(self, text: str, voice: str, speed: str) -> Dict:
        """Use gTTS as fallback"""
        try:
            if not GTTS_AVAILABLE:
                return {"success": False, "error": "gTTS not installed"}
            
            start_time = time.time()
            
            # Synthesize
            output_path = os.path.join(
                TTS_CONFIG["temp_dir"],
                f"gtts_{int(time.time()*1000)}.mp3"
            )
            
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(output_path)
            
            # Estimate duration (rough)
            word_count = len(text.split())
            estimated_duration = int((word_count / 150) * 60 * 1000)  # 150 WPM
            
            logger.info(f"gTTS synthesis successful: {estimated_duration}ms")
            
            return {
                "success": True,
                "audio_path": output_path,
                "duration_ms": estimated_duration,
                "engine": "gtts",
                "error": None
            }
        
        except Exception as e:
            logger.error(f"gTTS failed: {e}")
            return {
                "success": False,
                "audio_path": None,
                "duration_ms": 0,
                "engine": "gtts",
                "error": str(e)
            }
    
    def get_available_voices(self) -> Dict:
        """Get list of available voices"""
        voices = []
        
        if self.coqui_model:
            voices.extend([
                {
                    "id": "female",
                    "name": "Sarah (Female)",
                    "engine": "coqui",
                    "language": "en-US"
                },
                {
                    "id": "male",
                    "name": "David (Male)",
                    "engine": "coqui",
                    "language": "en-US"
                }
            ])
        
        if GTTS_AVAILABLE:
            voices.append({
                "id": "gtts",
                "name": "Google (Any)",
                "engine": "gtts",
                "language": "en-US"
            })
        
        return {
            "voices": voices,
            "speeds": [
                {"id": "slow", "multiplier": 0.8},
                {"id": "normal", "multiplier": 1.0},
                {"id": "fast", "multiplier": 1.2}
            ]
        }
    
    def _sanitize_text(self, text: str) -> str:
        """Remove dangerous characters and limit length"""
        # Remove HTML/JavaScript
        text = text.replace("<", "").replace(">", "").replace("{", "").replace("}", "")
        
        # Limit length
        if len(text) > 1000:
            text = text[:997] + "..."
        
        return text.strip()
    
    def _cache_result(self, key: str, result: Dict):
        """Cache synthesis result"""
        if TTS_CONFIG["cache_enabled"]:
            self.cache[key] = result
            
            # Simple LRU: if cache too large, clear oldest
            max_items = (TTS_CONFIG["cache_max_size_mb"] * 1024 * 1024) // 50000
            if len(self.cache) > max_items:
                # Remove oldest (simplistic FIFO)
                old_key = next(iter(self.cache))
                del self.cache[old_key]
    
    def cleanup_old_files(self, max_age_minutes: int = 5):
        """Delete temporary audio files older than max_age_minutes"""
        import time
        current_time = time.time()
        max_age_seconds = max_age_minutes * 60
        
        for file in Path(TTS_CONFIG["temp_dir"]).glob("*.wav"):
            file_age = current_time - os.path.getmtime(file)
            if file_age > max_age_seconds:
                try:
                    os.remove(file)
                    logger.info(f"Cleaned up old TTS file: {file}")
                except Exception as e:
                    logger.warning(f"Failed to clean up {file}: {e}")


# Global instance
tts_engine = None

def get_tts_engine() -> TTSEngine:
    """Get or create TTS engine instance"""
    global tts_engine
    if tts_engine is None:
        tts_engine = TTSEngine()
    return tts_engine
