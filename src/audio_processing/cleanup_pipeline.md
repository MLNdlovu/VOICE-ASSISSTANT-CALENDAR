# Audio Cleanup Pipeline Documentation

## Overview
Real-time audio preprocessing to clean microphone input before Speech Recognition.

## Why Audio Cleanup?

Raw microphone audio contains:
- ✅ Background noise (AC, fans, traffic)
- ✅ Room echo
- ✅ Microphone hum (50/60 Hz)
- ✅ Silence gaps
- ✅ Clipping/distortion

**Our cleanup removes this** → cleaner recognition.

## Processing Pipeline

### Stage 1: Noise Reduction
**Library**: `noisereduce`
**Purpose**: Remove constant background noise

```
Input Audio: [NOISE] "hello" [NOISE] "world" [NOISE]
                ↓
Noise Profile: Learn noise pattern from silence
                ↓
Output: "hello world" (noise removed)
```

**Parameters**:
- Noise profile: 500ms of silence
- Reduction strength: 0.5 (balanced)
- FFT size: 2048

**Returns**:
```python
{
    "audio_reduced": bytes,
    "noise_floor_db": -35,
    "reduction_amount_db": 8,
    "processing_time_ms": 45
}
```

### Stage 2: Silence Trimming
**Library**: `pydub`
**Purpose**: Remove silence before/after speech

```
Input: [SILENCE] "hello world" [SILENCE]
            ↓
Output: "hello world" (silence trimmed)
```

**Parameters**:
- Silence threshold: -40dB
- Min silence duration: 500ms before trim
- Padding: 100ms of silence kept

**Returns**:
```python
{
    "audio_trimmed": bytes,
    "silence_start_ms": 145,
    "silence_end_ms": 2300,
    "speech_start_ms": 145,
    "speech_end_ms": 2300
}
```

### Stage 3: Volume Normalization
**Purpose**: Set consistent volume level

```
Input: [QUIET] "hello" [LOUD] "world"
           ↓
Output: "hello" "world" (both at -20dB)
```

**Algorithm**:
- Target: -20dB RMS (peak comfortable listening)
- Method: Calculate RMS, adjust gain
- Peak limiting: -3dB to prevent clipping

**Returns**:
```python
{
    "audio_normalized": bytes,
    "original_db": -28,
    "normalized_db": -20,
    "gain_applied_db": 8,
    "peaks_clipped": 0
}
```

### Stage 4: Frequency Filtering
**Purpose**: Remove hum and other artifacts

```
Remove:
- 50/60 Hz hum (power line)
- Low rumble (< 80 Hz)
- High hiss (> 12 kHz)
Keep:
- Speech frequencies (80 Hz - 8 kHz)
```

**Filters Applied**:
1. High-pass filter (80 Hz) → removes rumble
2. Notch filter (60 Hz, 120 Hz) → removes hum
3. Low-pass filter (8 kHz) → removes hiss

**Returns**:
```python
{
    "audio_filtered": bytes,
    "filters_applied": ["highpass_80hz", "notch_60hz", "lowpass_8khz"],
    "processing_time_ms": 25
}
```

## Full Pipeline Function

### `cleanup_audio(audio_bytes, noise_profile=None)`
**Purpose**: Run full cleanup pipeline
**Parameters**:
- `audio_bytes` (bytes): Raw PCM audio
- `noise_profile` (optional): Pre-learned noise pattern

**Returns**:
```python
{
    "success": True,
    "audio_cleaned": bytes,
    "stages_applied": {
        "noise_reduction": {"reduction_db": 8},
        "silence_trimming": {"ms_removed": 300},
        "volume_normalization": {"gain_db": 8},
        "frequency_filtering": {"filters": 3}
    },
    "total_processing_time_ms": 120,
    "quality_score": 0.87
}
```

## Noise Profile Learning

### `learn_noise_profile(silence_sample)`
**Purpose**: Learn background noise pattern

Called once at app startup when no one is speaking.

```python
# Frontend captures 500ms of silence
const silenceSample = await recordSilence(500);

# Send to backend
const response = await fetch('/api/cleanup/learn_noise', {
    method: 'POST',
    body: silenceSample
});

# Backend learns pattern
{
    "noise_profile_learned": True,
    "noise_level_db": -35,
    "profile_id": "profile_abc123"
}
```

### When to Re-learn
- On app startup
- If environment changes (moved to different room)
- User clicks "Recalibrate" button
- Every 4 hours if app is still running

## Real-time Noise Monitoring

### `analyze_noise(audio_chunk)`
**Purpose**: Detect environment noise levels and classify
**Returns**:
```python
{
    "noise_level_db": -25,
    "noise_classification": "medium_ambient",
    "recommendation": "continue_recording",
    "details": {
        "ambient_noise": -28,
        "speech_estimate": -20,
        "signal_to_noise_ratio": 8
    }
}
```

### Noise Classifications
| Classification | dB Range | Action | Display |
|---|---|---|---|
| `silent` | < -50 | Pause listening | "Waiting for audio..." |
| `low_ambient` | -50 to -35 | Continue normally | ✓ Normal recording |
| `medium_ambient` | -35 to -20 | Continue with caution | ⚠️ Some noise detected |
| `high_background` | -20 to -10 | Pause and warn | ❌ Too much noise |
| `very_loud` | > -10 | Stop recording | 🔴 Move to quieter place |

## Frontend Integration

### Step 1: Learn Noise on Startup
```javascript
// User opens app, no one speaking yet
fetch('/api/cleanup/learn_noise', {
    method: 'POST',
    body: silenceBuffer
}).then(r => r.json()).then(data => {
    if (data.noise_profile_learned) {
        console.log('Noise profile learned');
        startListening();
    }
});
```

### Step 2: Monitor Noise During Recording
```javascript
mediaRecorder.ondataavailable = async (event) => {
    const chunk = event.data;
    
    // Analyze noise
    const noiseStatus = await fetch('/api/cleanup/analyze', {
        method: 'POST',
        body: chunk
    }).then(r => r.json());
    
    if (noiseStatus.recommendation === 'pause_recording') {
        pauseRecording();
        showNotification(`${noiseStatus.noise_classification}: Please move to a quieter place`);
    }
};
```

### Step 3: Clean Audio Before STT
```javascript
const cleanAudio = await fetch('/api/cleanup/process', {
    method: 'POST',
    body: JSON.stringify({
        audio: audioBuffer,
        apply_all_stages: true
    })
}).then(r => r.json());

// Send cleaned audio to STT
recognizeAudio(cleanAudio.audio_cleaned);
```

## Configuration

See application settings:
- Noise reduction strength
- Silence trim threshold
- Target volume level (-20dB)
- Filter frequencies
- Noise profile cache location

## Error Handling

### Pipeline Failures
```python
{
    "success": False,
    "stage_failed": "noise_reduction",
    "error": "noisereduce library not installed",
    "fallback": "use_raw_audio"
}
```

### Handling Failure
1. Log error
2. Return original audio
3. Continue processing (no TTS/STT blocking)
4. Notify admin in logs

## Performance

### Processing Time
- Noise reduction: ~40ms
- Silence trimming: ~10ms
- Volume normalization: ~10ms
- Frequency filtering: ~25ms
- **Total: ~85ms per 500ms audio chunk**

### Memory
- Noise profile: ~5KB
- Processing buffer: ~2MB per concurrent stream
- Cached profiles: ~50KB

## Testing

### Unit Tests
- [x] Noise reduction on various noise types
- [x] Silence trimming accuracy
- [x] Volume normalization to target
- [x] Filter frequency response
- [x] Noise profile learning

### Integration Tests
- [x] Full pipeline on noisy environment
- [x] Full pipeline on quiet environment
- [x] Real-time monitoring during recording
- [x] Error recovery

### Manual Tests
- [x] Record in noisy coffee shop
- [x] Record with AC running
- [x] Record with background TV
- [x] Record in quiet office
- [x] Verify cleanup improves STT accuracy

## Future Enhancements

1. **AI Noise Classification**: Identify noise type (barking, sirens, etc.)
2. **Adaptive Thresholds**: Auto-adjust noise threshold based on environment
3. **Echo Cancellation**: Remove room echo from recorded audio
4. **Voice Activity Detection**: Precise speech boundary detection
5. **Compression Optimization**: Compress audio before sending over network
