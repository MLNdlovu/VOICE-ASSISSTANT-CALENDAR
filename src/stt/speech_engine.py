"""
Speech Recognition Engine (STT) - Vosk Offline Model
Converts audio to text using Vosk with noise detection
"""

import os
import json
import logging
import numpy as np
from typing import Dict, Optional
from pathlib import Path

try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    Model = None
    KaldiRecognizer = None

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

logger = logging.getLogger(__name__)

# Configuration
STT_CONFIG = {
    "model_path": "/models/vosk_en/",
    "model_name": "vosk-model-en-us-0.22",
    "model_url": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip",
    "sample_rate": 16000,
    "chunk_size": 4096,
    "confidence_threshold": 0.6,
    "silence_threshold_db": -40,
    "silence_duration_ms": 1500,
    "noise_reduction_enabled": True
}


class STTEngine:
    """Speech-to-Text recognition with Vosk offline model"""
    
    def __init__(self):
        self.model = None
        self.recognizer = None
        self.model_loaded = False
        self.noise_profile = None
        self.initialize_model()
    
    def initialize_model(self):
        """Load Vosk model at startup"""
        if not VOSK_AVAILABLE:
            logger.error("Vosk not installed. Install with: pip install vosk")
            return
        
        # Check if model exists
        model_path = os.path.join(STT_CONFIG["model_path"], "model")
        
        if not os.path.exists(model_path):
            logger.warning(f"Model not found at {model_path}")
            logger.info("Attempting to download model...")
            self._download_model()
        
        try:
            logger.info(f"Loading Vosk model from {model_path}...")
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, STT_CONFIG["sample_rate"])
            self.model_loaded = True
            logger.info("✓ Vosk model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Vosk model: {e}")
            self.model_loaded = False
    
    def _download_model(self):
        """Download Vosk model on first run"""
        try:
            import urllib.request
            import zipfile
            import shutil
            
            logger.info("Downloading Vosk English model (~50MB)...")
            
            model_dir = STT_CONFIG["model_path"]
            os.makedirs(model_dir, exist_ok=True)
            
            zip_path = os.path.join(model_dir, "model.zip")
            
            # Download
            urllib.request.urlretrieve(
                STT_CONFIG["model_url"],
                zip_path,
                reporthook=self._download_progress
            )
            
            # Extract
            logger.info("Extracting model...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(model_dir)
            
            # Cleanup zip
            os.remove(zip_path)
            
            logger.info("✓ Model downloaded successfully")
        
        except Exception as e:
            logger.error(f"Failed to download model: {e}")
    
    def _download_progress(self, block_num, block_size, total_size):
        """Report download progress"""
        downloaded = block_num * block_size
        percent = min(downloaded * 100 // total_size, 100)
        logger.info(f"Download progress: {percent}%")
    
    def recognize_speech(self, audio_chunk: bytes) -> Dict:
        """
        Process audio chunk for speech recognition
        
        Args:
            audio_chunk: Raw PCM audio bytes (16-bit)
        
        Returns:
            {
                "result": str,
                "confidence": float (0.0-1.0),
                "is_final": bool,
                "is_silent": bool,
                "is_noise": bool,
                "timestamp": float
            }
        """
        import time
        
        if not self.model_loaded:
            return {
                "result": "model_not_loaded",
                "confidence": 0.0,
                "is_final": False,
                "is_silent": False,
                "is_noise": False,
                "timestamp": time.time(),
                "error": "STT model not loaded"
            }
        
        try:
            # Process audio
            self.recognizer.AcceptWaveform(audio_chunk)
            result_json = self.recognizer.Result()
            
            # Parse result
            if result_json:
                result_dict = json.loads(result_json)
            else:
                result_dict = {}
            
            # Get partial result
            partial = result_dict.get('partial', '')
            final = result_dict.get('result', [])
            
            # Build response
            is_final = len(final) > 0
            text = ' '.join(final) if is_final else partial
            
            # Estimate confidence
            confidence = 0.85 if is_final and text else 0.5 if partial else 0.0
            
            # Detect silence
            silence_result = self.detect_silence(audio_chunk)
            is_silent = silence_result["is_silent"]
            
            # Detect noise
            noise_result = self.detect_noise(audio_chunk)
            is_noise = noise_result["is_noise"]
            
            return {
                "result": text if text else ("no speech detected" if is_silent else ""),
                "confidence": confidence,
                "is_final": is_final,
                "is_silent": is_silent,
                "is_noise": is_noise,
                "timestamp": time.time()
            }
        
        except Exception as e:
            logger.error(f"Recognition failed: {e}")
            return {
                "result": "recognition_error",
                "confidence": 0.0,
                "is_final": False,
                "is_silent": False,
                "is_noise": False,
                "timestamp": time.time(),
                "error": str(e)
            }
    
    def detect_silence(self, audio_chunk: bytes, threshold_db: int = -40) -> Dict:
        """
        Detect if audio is silent
        
        Args:
            audio_chunk: Raw PCM audio
            threshold_db: Silence threshold
        
        Returns:
            {
                "is_silent": bool,
                "silence_duration_ms": float,
                "volume_db": float
            }
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
            
            # Calculate RMS (volume)
            rms = np.sqrt(np.mean(audio_array ** 2))
            
            # Convert to dB
            if rms > 0:
                volume_db = 20 * np.log10(rms)
            else:
                volume_db = -100
            
            is_silent = volume_db < threshold_db
            silence_duration_ms = (len(audio_chunk) / 2) / (STT_CONFIG["sample_rate"] / 1000)
            
            return {
                "is_silent": is_silent,
                "silence_duration_ms": silence_duration_ms,
                "volume_db": volume_db
            }
        
        except Exception as e:
            logger.error(f"Silence detection failed: {e}")
            return {
                "is_silent": True,
                "silence_duration_ms": 0,
                "volume_db": -100
            }
    
    def detect_noise(self, audio_chunk: bytes, threshold: float = 0.3) -> Dict:
        """
        Classify background noise vs speech
        
        Args:
            audio_chunk: Raw PCM audio
            threshold: Noise threshold (0.0-1.0)
        
        Returns:
            {
                "is_noise": bool,
                "noise_score": float (0.0-1.0),
                "noise_type": str,
                "recommendation": str
            }
        """
        try:
            audio_array = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
            
            # Simple frequency analysis
            # High-frequency energy suggests noise
            fft = np.abs(np.fft.fft(audio_array))
            
            # Ratio of high-freq to low-freq energy
            high_freq_energy = np.sum(fft[len(fft)//2:])
            low_freq_energy = np.sum(fft[:len(fft)//2])
            
            if low_freq_energy > 0:
                noise_ratio = high_freq_energy / low_freq_energy
            else:
                noise_ratio = 0
            
            # Classify
            is_noise = noise_ratio > threshold
            
            # Determine noise type
            if noise_ratio < 0.1:
                noise_type = "speech"
            elif noise_ratio < 0.2:
                noise_type = "low_ambient"
            elif noise_ratio < 0.4:
                noise_type = "medium_ambient"
            else:
                noise_type = "high_background"
            
            # Recommendation
            if is_noise and noise_ratio > 0.6:
                recommendation = "pause_recording"
            elif is_noise:
                recommendation = "continue_with_caution"
            else:
                recommendation = "continue_recording"
            
            return {
                "is_noise": is_noise,
                "noise_score": min(noise_ratio, 1.0),
                "noise_type": noise_type,
                "recommendation": recommendation
            }
        
        except Exception as e:
            logger.error(f"Noise detection failed: {e}")
            return {
                "is_noise": False,
                "noise_score": 0.0,
                "noise_type": "unknown",
                "recommendation": "continue_recording"
            }
    
    def learn_noise_profile(self, silence_sample: bytes):
        """Learn ambient noise profile from silence"""
        try:
            audio_array = np.frombuffer(silence_sample, dtype=np.int16).astype(np.float32)
            fft = np.abs(np.fft.fft(audio_array))
            
            self.noise_profile = {
                "fft": fft.tolist(),
                "energy": float(np.mean(audio_array ** 2)),
                "timestamp": time.time()
            }
            
            logger.info("Noise profile learned")
            return {"success": True, "profile_id": "profile_current"}
        
        except Exception as e:
            logger.error(f"Failed to learn noise profile: {e}")
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict:
        """Get STT engine status"""
        return {
            "model_loaded": self.model_loaded,
            "vosk_available": VOSK_AVAILABLE,
            "model_path": STT_CONFIG["model_path"],
            "sample_rate": STT_CONFIG["sample_rate"],
            "confidence_threshold": STT_CONFIG["confidence_threshold"]
        }


# Global instance
stt_engine = None

def get_stt_engine() -> STTEngine:
    """Get or create STT engine instance"""
    global stt_engine
    if stt_engine is None:
        stt_engine = STTEngine()
    return stt_engine
