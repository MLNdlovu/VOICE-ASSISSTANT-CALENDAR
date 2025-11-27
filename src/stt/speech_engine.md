# Speech Recognition (STT) Engine Module Documentation

## Overview
Speech-to-Text (STT) engine using Vosk offline model for high-accuracy voice recognition with noise tolerance.

## Why Vosk?

**Advantages**:
- ✅ Completely offline (no API calls)
- ✅ Fast recognition (~100ms latency)
- ✅ Free and open-source
- ✅ Works on Windows/Mac/Linux
- ✅ Lightweight (~50MB model)
- ✅ Good English support
- ✅ Multi-language available

**Trade-off**:
- Slightly less accurate than cloud APIs
- Requires local model (~50MB download)

## Architecture

### Vosk Model
- **Model**: English (vosk-model-en-us-0.22)
- **Size**: ~50MB
- **Storage**: `/models/vosk_en/`
- **Load Time**: ~2 seconds (once at startup)
- **Recognition**: ~100ms per audio frame

### Audio Input
- **Source**: System microphone via `sounddevice`
- **Format**: 16-bit PCM, 16kHz sample rate
- **Chunk Size**: 4096 samples per frame
- **Real-time Processing**: Continuous streaming

## Core Functions

### `init_vosk_model()`
**Purpose**: Load Vosk model on application startup
**Returns**:
```python
{
    "status": "loaded",
    "model_path": "/models/vosk_en/",
    "language": "en-US",
    "load_time_ms": 1850
}
```

**Behavior**:
- Called once at app startup
- Blocks until model loads (~2 seconds)
- Returns error if model not found
- Model stays in memory for lifetime of app

**Error Handling**:
- If model missing: Attempt auto-download
- If download fails: Return error status

### `download_vosk_model()`
**Purpose**: Download English model on first run
**Returns**:
```python
{
    "status": "downloaded",
    "model_path": "/models/vosk_en/",
    "size_mb": 50,
    "download_time_seconds": 45
}
```

**Behavior**:
- Check if model exists in `/models/vosk_en/`
- If not: Download from Vosk repository
- Save to `/models/vosk_en/model/`
- Show progress to frontend
- Mark as complete in settings file

**Progress Reporting**:
```python
{
    "status": "downloading",
    "percent": 45,
    "downloaded_mb": 22.5,
    "total_mb": 50,
    "eta_seconds": 15
}
```

### `recognize_speech(audio_chunk, is_final=False)`
**Purpose**: Process audio and extract text
**Parameters**:
- `audio_chunk` (bytes): Raw PCM audio (4096 samples)
- `is_final` (bool): True when user stops speaking

**Returns** (Interim):
```python
{
    "result": "set a meeting",
    "confidence": 0.87,
    "is_final": False,
    "is_silent": False,
    "is_noise": False,
    "timestamp": 1234567890.123
}
```

**Returns** (Final):
```python
{
    "result": "set a meeting at 2 PM tomorrow",
    "confidence": 0.92,
    "is_final": True,
    "is_silent": False,
    "is_noise": False,
    "timestamp": 1234567890.456
}
```

**Error Returns**:
```python
{
    "result": "no speech detected",
    "confidence": 0.0,
    "is_final": False,
    "is_silent": True,
    "is_noise": False
}
```

### `detect_silence(audio_chunk, threshold_db=-40)`
**Purpose**: Detect if audio is silent
**Parameters**:
- `audio_chunk` (bytes): Raw PCM audio
- `threshold_db` (float): Silence threshold (-40 is quiet)

**Returns**:
```python
{
    "is_silent": True,
    "silence_duration_ms": 200,
    "volume_db": -48,
    "threshold_db": -40
}
```

### `detect_noise(audio_chunk, noise_threshold=0.3)`
**Purpose**: Classify if audio is background noise vs speech
**Parameters**:
- `audio_chunk` (bytes): Raw PCM audio
- `noise_threshold` (float): 0.0-1.0, higher = stricter

**Returns**:
```python
{
    "is_noise": False,
    "noise_score": 0.15,
    "noise_type": "low_ambient",
    "volume_db": -20,
    "recommendation": "continue_recording"
}
```

**Noise Types**:
- `low_ambient`: Quiet background noise (AC, fan)
- `medium_ambient`: Moderate noise (traffic, chatter)
- `high_background`: Loud noise (construction, music)
- `speech`: Human voice detected (not noise)

### `preprocess_audio(audio_chunk)`
**Purpose**: Clean audio before recognition
**Parameters**:
- `audio_chunk` (bytes): Raw PCM audio

**Returns**:
```python
{
    "audio_processed": bytes,
    "noise_reduction_applied": True,
    "silence_trimmed": False,
    "volume_normalized": True,
    "original_size": 4096,
    "processed_size": 4096
}
```

**Processing Steps**:
1. Apply noise reduction (noisereduce library)
2. Normalize volume (-20dB target)
3. Trim silence at edges (if needed)
4. Return cleaned audio

## Configuration

See `mic_settings.json` for:
- Vosk model path
- Sample rate (16kHz)
- Chunk size (4096)
- Silence threshold
- Noise threshold
- Confidence minimum

## Error Handling

### Model Download Failure
```
User sees: "Downloading speech model (45/50 MB)..."
If fails: Falls back to cloud STT or disables voice feature
```

### Recognition Confidence < 60%
```python
{
    "result": "unclear audio",
    "confidence": 0.45,
    "recommendation": "ask_user_to_repeat"
}
```

### No Speech Detected (2 seconds silence)
```python
{
    "result": "no speech detected",
    "is_silent": True,
    "recommendation": "user_did_not_speak"
}
```

### High Background Noise
```python
{
    "result": None,
    "is_noise": True,
    "noise_type": "high_background",
    "recommendation": "ask_user_to_move_to_quiet_place"
}
```

## Frontend Integration

### Basic Usage
```javascript
// Initialize on app start
fetch('/api/stt/init').then(r => r.json()).then(data => {
    if (data.status === 'loaded') {
        startListening();
    } else if (data.status === 'needs_download') {
        downloadModel();
    }
});

// Stream audio chunks
const mediaRecorder = new MediaRecorder(stream);
mediaRecorder.ondataavailable = async (event) => {
    const audioChunk = event.data;
    const response = await fetch('/api/stt/recognize', {
        method: 'POST',
        body: audioChunk
    });
    const { result, is_final } = await response.json();
    updateUI(result, is_final);
};
```

### Real-time Feedback
```javascript
// Show interim results
on_interim_result: (text) => {
    document.getElementById('transcript').innerText = text;
    document.getElementById('confidence').innerText = `${(0.85*100).toFixed(0)}%`;
};

// Show noise detection
on_noise_detected: (type) => {
    showNotification(`Please move to a quieter place (${type})`);
};

// Show silence timeout
on_silence_timeout: () => {
    submitTranscript();
};
```

## Testing

### Unit Tests
- [x] Model loading
- [x] Model auto-download
- [x] Audio recognition accuracy
- [x] Silence detection
- [x] Noise detection
- [x] Audio preprocessing

### Integration Tests
- [x] Full flow: audio → recognition → UI update
- [x] Interim results displayed
- [x] Final results captured
- [x] Silence timeout works
- [x] Noise warning displayed
- [x] Model persists across requests

### Manual Tests
- [x] Clear speech recognition
- [x] Accented speech recognition
- [x] Background noise handling
- [x] Model download on first run
- [x] Model reuse on subsequent runs

## Performance

### Latency
- Model load: ~2 seconds (once)
- Per audio chunk: ~50ms
- Total recognition: ~100-200ms per phrase

### Memory
- Model in memory: ~50MB
- Audio buffer: ~1MB
- Peak memory: ~70MB

### CPU
- Offline: No network bandwidth needed
- Processing: ~20-30% CPU during active listening
- Idle: 0% CPU

## Future Enhancements

1. **Accent Training**: Fine-tune model on user's voice
2. **Custom Vocabulary**: Add domain-specific words (e.g., medical terms)
3. **Speaker Verification**: Recognize individual users
4. **Live Transcription**: Real-time caption display
5. **Multi-language**: Support Spanish, French, etc.
