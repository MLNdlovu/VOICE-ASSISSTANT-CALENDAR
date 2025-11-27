# TTS Engine Module Documentation

## Overview
Text-to-Speech (TTS) engine for converting assistant responses to natural audio using Coqui TTS with gTTS fallback.

## Architecture

### Primary Engine: Coqui TTS
- **Library**: `coqui-tts`
- **Quality**: High naturalness, minimal robotic artifacts
- **Speed**: ~2 seconds for typical responses
- **Voices Available**:
  - Female (default): Glow-TTS trained on LJSpeech
  - Male: Glow-TTS trained on VCTK
  - Custom: Can train on user voice samples (future)

### Fallback Engine: gTTS
- **Trigger**: When Coqui fails or unavailable
- **Library**: `gtts`
- **Quality**: Medium (functional but slightly robotic)
- **Speed**: Fast (cached by Google)
- **Voices**: Limited, but multilingual support

## Core Functions

### `synthesize_text(text, voice="female", speed="normal")`
**Purpose**: Convert assistant text to audio
**Parameters**:
- `text` (str): Assistant response
- `voice` (str): "male" or "female"
- `speed` (str): "slow" (0.8), "normal" (1.0), "fast" (1.2)

**Returns**:
```python
{
    "success": bool,
    "audio_path": "/tmp/tts_xxxx.wav",
    "duration_ms": int,
    "engine": "coqui" | "gtts" | "error",
    "error": str | null
}
```

**Error Handling**:
- Try Coqui first
- Fall back to gTTS on Coqui failure
- Return plain text on total failure

### `synthesize_with_timing(assistant_text, spoken_time, voice="female", speed="normal")`
**Purpose**: TTS that emphasizes spoken time
**Parameters**:
- `assistant_text` (str): Main response
- `spoken_time` (str): Time to emphasize (e.g., "2 PM")
- `voice` (str): Voice selection
- `speed` (str): Speech rate

**Behavior**:
- Insert slight pause before spoken_time
- Use slightly higher pitch for spoken_time
- Return combined audio file

**Returns**: Same as `synthesize_text()`

### `set_voice_settings(user_id, voice, speed, gender)`
**Purpose**: Save user's TTS preferences
**Parameters**:
- `user_id` (str): User identifier
- `voice` (str): "male" | "female"
- `speed` (str): "slow" | "normal" | "fast"
- `gender` (str): "male" | "female" | "default"

**Storage**: LocalStorage on frontend (no backend persistence)

**Returns**:
```python
{"ok": true, "message": "Voice settings updated"}
```

### `get_available_voices()`
**Purpose**: List available voice options
**Returns**:
```python
{
    "voices": [
        {"id": "female", "name": "Sarah (Female)", "language": "en-US", "engine": "coqui"},
        {"id": "male", "name": "David (Male)", "language": "en-US", "engine": "coqui"},
        {"id": "gtts_female", "name": "Google (Female)", "language": "en-US", "engine": "gtts"}
    ],
    "speeds": ["slow", "normal", "fast"]
}
```

## Audio Output Formats

### WAV File (Default)
- **Format**: 22.05kHz, 16-bit mono
- **Storage**: `/tmp/tts_<timestamp>.wav`
- **Lifetime**: Deleted after 5 minutes
- **Transport**: Streamed to frontend via `/api/tts`

### Base64 Blob (API Response)
- **Format**: Base64-encoded PCM audio
- **Use Case**: Inline playback without extra HTTP request
- **Size**: ~50KB for typical 5-second response
- **Transport**: JSON response body

## Configuration

See `voice_settings.json` for:
- Default voice gender
- Default speech rate
- Engine preferences
- Audio format selection
- Cache configuration

## Error Handling

### Fallback Chain
```
Coqui TTS (primary)
  ↓ (fails)
gTTS (secondary)
  ↓ (fails)
Plain text response (no audio)
```

### Error Messages to Frontend
```python
{
    "success": false,
    "engine": "error",
    "fallback_text": "I couldn't speak that, but here is your response.",
    "error": "Detailed error message for logging"
}
```

### Common Failure Scenarios
1. **Text too long** (>500 chars): Truncate at sentence boundary
2. **Special characters**: Replace with readable alternatives
3. **No audio device**: Return JSON with `engine: "error"`
4. **Network timeout**: Use cached audio or gTTS

## Performance Considerations

### Caching
- Cache synthesized audio for repeated phrases
- Cache limit: 100MB
- TTL: 24 hours

### Streaming
- Stream audio in chunks (500ms)
- Don't wait for full synthesis before streaming
- Frontend starts playback after 200ms

### Concurrency
- Max 3 concurrent TTS operations
- Queue additional requests
- Timeout after 30 seconds

## Security

### Input Validation
- Sanitize text for injection attacks
- Remove HTML/JavaScript
- Limit text length to 1000 characters

### Audio File Lifecycle
- Delete temporary files after 5 minutes
- Never store on disk for production
- Use in-memory buffer when possible

## Frontend Integration

### Basic Usage
```javascript
const response = await fetch('/api/tts', {
    method: 'POST',
    body: JSON.stringify({
        text: "Your calendar event is set",
        voice: "female",
        speed: "normal"
    })
});
const audio = await response.blob();
playAudio(audio);
```

### Advanced Usage
```javascript
const response = await fetch('/api/tts', {
    method: 'POST',
    body: JSON.stringify({
        text: "You have a meeting at 2 PM",
        spoken_time: "2 PM",
        voice: "female",
        speed: "normal",
        format: "base64"
    })
});
const { audio_base64 } = await response.json();
playBase64Audio(audio_base64);
```

## Testing

### Unit Tests
- Test Coqui engine with various text lengths
- Test gTTS fallback
- Test voice switching
- Test error conditions

### Integration Tests
- Test full pipeline: text → audio → frontend playback
- Test concurrent requests
- Test cache effectiveness
- Test special characters

### Manual Testing
- Verify naturalness of voice
- Verify timing accuracy
- Verify fallback behavior
- Verify audio quality

## Future Enhancements

1. **Custom Voice Training**: Allow users to train voice on their own audio
2. **Emotion Detection**: Adjust pitch/rate based on sentiment
3. **Background Music**: Optional background music behind TTS
4. **Voice Cloning**: Clone user's voice for greeting
5. **Multiple Languages**: Support non-English languages
