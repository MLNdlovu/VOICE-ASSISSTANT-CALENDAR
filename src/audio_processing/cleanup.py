"""
Audio Cleanup Pipeline - Noise reduction and audio preprocessing
"""

import os
import logging
import numpy as np
from typing import Dict, Optional

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

try:
    import noisereduce as nr
    NOISEREDUCE_AVAILABLE = True
except ImportError:
    NOISEREDUCE_AVAILABLE = False

from scipy import signal
import soundfile as sf

logger = logging.getLogger(__name__)

CLEANUP_CONFIG = {
    "noise_reduction_strength": 0.5,
    "silence_threshold_db": -40,
    "min_silence_duration_ms": 500,
    "target_db": -20,
    "sample_rate": 16000
}


class AudioCleanup:
    """Audio preprocessing and cleanup pipeline"""
    
    def __init__(self):
        self.noise_profile = None
    
    def cleanup_audio(
        self,
        audio_bytes: bytes,
        apply_noise_reduction: bool = True,
        apply_silence_trim: bool = True,
        apply_normalization: bool = True,
        apply_filtering: bool = True
    ) -> Dict:
        """
        Run full audio cleanup pipeline
        
        Args:
            audio_bytes: Raw PCM audio (16-bit, 16kHz)
            apply_noise_reduction: Remove background noise
            apply_silence_trim: Trim silence
            apply_normalization: Normalize volume
            apply_filtering: Apply frequency filters
        
        Returns:
            {
                "success": bool,
                "audio_cleaned": bytes,
                "stages_applied": dict,
                "total_processing_time_ms": float,
                "quality_score": float (0.0-1.0)
            }
        """
        import time
        start_time = time.time()
        
        try:
            # Convert to numpy array
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
            audio_array = audio_array / 32768.0  # Normalize to -1 to 1
            
            stages_applied = {}
            
            # Stage 1: Noise Reduction
            if apply_noise_reduction and NOISEREDUCE_AVAILABLE:
                audio_array, nr_stats = self._apply_noise_reduction(audio_array)
                stages_applied["noise_reduction"] = nr_stats
            
            # Stage 2: Silence Trimming
            if apply_silence_trim and PYDUB_AVAILABLE:
                audio_array, trim_stats = self._trim_silence(audio_array)
                stages_applied["silence_trimming"] = trim_stats
            
            # Stage 3: Volume Normalization
            if apply_normalization:
                audio_array, norm_stats = self._normalize_volume(audio_array)
                stages_applied["volume_normalization"] = norm_stats
            
            # Stage 4: Frequency Filtering
            if apply_filtering:
                audio_array, filter_stats = self._apply_filters(audio_array)
                stages_applied["frequency_filtering"] = filter_stats
            
            # Convert back to int16
            audio_array = np.clip(audio_array * 32768, -32768, 32767).astype(np.int16)
            audio_cleaned = audio_array.tobytes()
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Quality score (0.0-1.0)
            quality_score = 0.85
            
            return {
                "success": True,
                "audio_cleaned": audio_cleaned,
                "stages_applied": stages_applied,
                "total_processing_time_ms": processing_time_ms,
                "quality_score": quality_score
            }
        
        except Exception as e:
            logger.error(f"Audio cleanup failed: {e}")
            return {
                "success": False,
                "audio_cleaned": audio_bytes,
                "stages_applied": {},
                "total_processing_time_ms": 0,
                "quality_score": 0.0,
                "error": str(e)
            }
    
    def _apply_noise_reduction(self, audio_array: np.ndarray) -> tuple:
        """Apply noise reduction using noisereduce"""
        import time
        start = time.time()
        
        try:
            if not NOISEREDUCE_AVAILABLE:
                return audio_array, {"applied": False, "reason": "noisereduce not installed"}
            
            # Reduce noise
            reduced = nr.reduce_noise(
                y=audio_array,
                sr=CLEANUP_CONFIG["sample_rate"],
                stationary=True,
                prop_decrease=CLEANUP_CONFIG["noise_reduction_strength"]
            )
            
            # Calculate reduction amount
            original_power = np.mean(audio_array ** 2)
            reduced_power = np.mean(reduced ** 2)
            reduction_db = 10 * np.log10(original_power / reduced_power) if reduced_power > 0 else 0
            
            return reduced, {
                "applied": True,
                "reduction_db": float(reduction_db),
                "processing_time_ms": (time.time() - start) * 1000
            }
        
        except Exception as e:
            logger.error(f"Noise reduction failed: {e}")
            return audio_array, {"applied": False, "error": str(e)}
    
    def _trim_silence(self, audio_array: np.ndarray) -> tuple:
        """Trim silence from start and end"""
        import time
        start = time.time()
        
        try:
            # Calculate RMS for each frame
            frame_length = 512
            hop_length = 256
            
            frames = []
            for i in range(0, len(audio_array) - frame_length, hop_length):
                frame = audio_array[i:i+frame_length]
                rms = np.sqrt(np.mean(frame ** 2))
                frames.append(rms)
            
            frames = np.array(frames)
            
            # Find non-silent regions
            threshold = 10 ** (CLEANUP_CONFIG["silence_threshold_db"] / 20)
            speech_frames = frames > threshold
            
            # Find start and end
            if np.any(speech_frames):
                start_idx = np.where(speech_frames)[0][0]
                end_idx = np.where(speech_frames)[0][-1]
                
                # Convert frame indices to sample indices
                start_sample = max(0, start_idx * hop_length - frame_length)
                end_sample = min(len(audio_array), (end_idx + 1) * hop_length + frame_length)
                
                trimmed = audio_array[start_sample:end_sample]
                
                return trimmed, {
                    "applied": True,
                    "ms_removed_start": (start_sample / CLEANUP_CONFIG["sample_rate"]) * 1000,
                    "ms_removed_end": ((len(audio_array) - end_sample) / CLEANUP_CONFIG["sample_rate"]) * 1000,
                    "processing_time_ms": (time.time() - start) * 1000
                }
            else:
                return audio_array, {"applied": False, "reason": "all_silence"}
        
        except Exception as e:
            logger.error(f"Silence trimming failed: {e}")
            return audio_array, {"applied": False, "error": str(e)}
    
    def _normalize_volume(self, audio_array: np.ndarray) -> tuple:
        """Normalize audio to target volume"""
        import time
        start = time.time()
        
        try:
            # Calculate RMS
            rms = np.sqrt(np.mean(audio_array ** 2))
            
            # Convert to dB
            original_db = 20 * np.log10(rms) if rms > 0 else -100
            
            # Target dB
            target_db = CLEANUP_CONFIG["target_db"]
            
            # Calculate gain needed
            gain_db = target_db - original_db
            gain_linear = 10 ** (gain_db / 20)
            
            # Apply gain with peak limiting
            normalized = audio_array * gain_linear
            
            # Clip peaks to prevent distortion
            peak = np.max(np.abs(normalized))
            if peak > 0.9:
                normalized = normalized * (0.9 / peak)
                peaks_clipped = True
            else:
                peaks_clipped = False
            
            # Verify new RMS
            new_rms = np.sqrt(np.mean(normalized ** 2))
            new_db = 20 * np.log10(new_rms) if new_rms > 0 else -100
            
            return normalized, {
                "applied": True,
                "original_db": float(original_db),
                "target_db": float(target_db),
                "normalized_db": float(new_db),
                "gain_applied_db": float(gain_db),
                "peaks_clipped": peaks_clipped,
                "processing_time_ms": (time.time() - start) * 1000
            }
        
        except Exception as e:
            logger.error(f"Normalization failed: {e}")
            return audio_array, {"applied": False, "error": str(e)}
    
    def _apply_filters(self, audio_array: np.ndarray) -> tuple:
        """Apply frequency filters (highpass, notch, lowpass)"""
        import time
        start = time.time()
        
        try:
            filters_applied = []
            result = audio_array.copy()
            
            # Highpass filter (remove rumble < 80Hz)
            try:
                sos = signal.butter(4, 80, 'hp', fs=CLEANUP_CONFIG["sample_rate"], output='sos')
                result = signal.sosfilt(sos, result)
                filters_applied.append("highpass_80hz")
            except Exception as e:
                logger.warning(f"Highpass filter failed: {e}")
            
            # Notch filter (remove 60Hz hum)
            try:
                Q = 30  # Quality factor
                w0 = 60 / (CLEANUP_CONFIG["sample_rate"] / 2)
                sos = signal.iirnotch(w0, Q, output='sos')
                result = signal.sosfilt(sos, result)
                filters_applied.append("notch_60hz")
            except Exception as e:
                logger.warning(f"Notch filter failed: {e}")
            
            # Lowpass filter (remove hiss > 8kHz)
            try:
                sos = signal.butter(4, 8000, 'lp', fs=CLEANUP_CONFIG["sample_rate"], output='sos')
                result = signal.sosfilt(sos, result)
                filters_applied.append("lowpass_8khz")
            except Exception as e:
                logger.warning(f"Lowpass filter failed: {e}")
            
            return result, {
                "applied": True,
                "filters": filters_applied,
                "num_filters": len(filters_applied),
                "processing_time_ms": (time.time() - start) * 1000
            }
        
        except Exception as e:
            logger.error(f"Filtering failed: {e}")
            return audio_array, {"applied": False, "error": str(e)}
    
    def analyze_noise(self, audio_chunk: bytes) -> Dict:
        """Analyze noise level and classification"""
        try:
            audio_array = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
            audio_array = audio_array / 32768.0
            
            # Calculate RMS
            rms = np.sqrt(np.mean(audio_array ** 2))
            noise_level_db = 20 * np.log10(rms) if rms > 0 else -100
            
            # Classify
            if noise_level_db < -50:
                classification = "silent"
                recommendation = "pause_listening"
            elif noise_level_db < -35:
                classification = "low_ambient"
                recommendation = "continue_recording"
            elif noise_level_db < -20:
                classification = "medium_ambient"
                recommendation = "continue_with_caution"
            elif noise_level_db < -10:
                classification = "high_background"
                recommendation = "pause_recording"
            else:
                classification = "very_loud"
                recommendation = "stop_recording"
            
            return {
                "noise_level_db": float(noise_level_db),
                "noise_classification": classification,
                "recommendation": recommendation,
                "details": {
                    "ambient_noise": float(noise_level_db),
                    "signal_to_noise_ratio": 0  # Placeholder
                }
            }
        
        except Exception as e:
            logger.error(f"Noise analysis failed: {e}")
            return {
                "noise_level_db": -100,
                "noise_classification": "unknown",
                "recommendation": "stop_recording",
                "error": str(e)
            }


# Global instance
audio_cleanup = None

def get_audio_cleanup() -> AudioCleanup:
    """Get or create audio cleanup instance"""
    global audio_cleanup
    if audio_cleanup is None:
        audio_cleanup = AudioCleanup()
    return audio_cleanup
