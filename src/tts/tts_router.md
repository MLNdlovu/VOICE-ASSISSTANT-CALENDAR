# TTS Router - API Endpoints

## Endpoint: POST /api/tts

### Purpose
Convert assistant response text to natural audio

### Request
```json
{
    "text": "Your meeting is scheduled for 2 PM",
    "spoken_time": "2 PM",
    "voice": "female",
    "speed": "normal",
    "format": "wav"
}
```

**Parameters**:
- `text` (required, str): Assistant response text (max 1000 chars)
- `spoken_time` (optional, str): Time phrase to emphasize
- `voice` (optional, str): "female" | "male" (default: "female")
- `speed` (optional, str): "slow" | "normal" | "fast" (default: "normal")
- `format` (optional, str): "wav" | "base64" (default: "wav")

### Response - Success (WAV)
```
Content-Type: audio/wav
Content-Length: 45230
Content-Disposition: attachment; filename="tts_1234567890.wav"
<binary WAV data>
```

### Response - Success (Base64)
```json
{
    "success": true,
    "engine": "coqui",
    "audio_base64": "UklGRiYAAABXQVZFZm10IBAAAAABAAEA...",
    "duration_ms": 2500,
    "format": "base64"
}
```

### Response - Failure
```json
{
    "success": false,
    "engine": "error",
    "fallback_text": "I couldn't speak that, but here is your response.",
    "error": "TTS service unavailable",
    "text": "Your meeting is scheduled for 2 PM"
}
```

### Error Codes
- `400`: Invalid text or parameters
- `413`: Text too long (>1000 chars)
- `503`: All TTS engines unavailable
- `504`: Timeout (>30 seconds)

---

## Endpoint: POST /api/tts/voices

### Purpose
Get available voice options

### Request
```json
{}
```

### Response
```json
{
    "voices": [
        {
            "id": "female",
            "name": "Sarah (Female)",
            "engine": "coqui",
            "language": "en-US",
            "pitch_range": [0.8, 2.0]
        },
        {
            "id": "male",
            "name": "David (Male)",
            "engine": "coqui",
            "language": "en-US",
            "pitch_range": [0.5, 1.5]
        }
    ],
    "speeds": [
        {"id": "slow", "multiplier": 0.8},
        {"id": "normal", "multiplier": 1.0},
        {"id": "fast", "multiplier": 1.2}
    ]
}
```

---

## Endpoint: POST /api/tts/settings

### Purpose
Update user's TTS preferences

### Request
```json
{
    "voice": "female",
    "speed": "normal"
}
```

### Response
```json
{
    "ok": true,
    "message": "Voice settings saved to localStorage"
}
```

---

## Endpoint: GET /api/tts/health

### Purpose
Check TTS service status

### Response
```json
{
    "status": "healthy",
    "coqui": {
        "available": true,
        "models_loaded": true,
        "last_synthesis_ms": 2450
    },
    "gtts": {
        "available": true,
        "latency_ms": 850
    },
    "timestamp": "2025-11-25T10:30:45Z"
}
```

---

## Implementation Flow

### POST /api/tts Processing Pipeline

```python
@app.route('/api/tts', methods=['POST'])
def synthesize():
    try:
        # 1. Validate input
        data = request.json
        text = sanitize_text(data['text'])
        validate_text_length(text)
        
        # 2. Get user preferences
        voice = data.get('voice', 'female')
        speed = data.get('speed', 'normal')
        format = data.get('format', 'wav')
        
        # 3. Check cache
        cache_key = hash(text + voice + speed)
        cached = get_cache(cache_key)
        if cached:
            return stream_audio(cached, format)
        
        # 4. Synthesize audio
        audio_result = synthesize_text(text, voice, speed)
        
        # 5. Handle errors
        if not audio_result['success']:
            return error_response(audio_result)
        
        # 6. Cache result
        cache_audio(cache_key, audio_result['audio_path'])
        
        # 7. Return audio
        if format == 'base64':
            return json_response(audio_result)
        else:
            return stream_audio(audio_result['audio_path'], 'wav')
            
    except Exception as e:
        log_error(e)
        return error_response({
            'engine': 'error',
            'error': str(e)
        })
```

### Key Decision Points

1. **Primary vs Fallback**
   - Try Coqui first (quality)
   - Fall back to gTTS (reliability)

2. **Format Selection**
   - `wav`: Ideal for streaming playback
   - `base64`: Useful for offline handling

3. **Caching Strategy**
   - Cache successful syntheses
   - Invalidate on settings change
   - Implement LRU eviction

4. **Error Response**
   - Never return empty audio
   - Always provide fallback text
   - Log error for debugging

---

## Frontend Integration

### HTML
```html
<audio id="tts-player" preload="none"></audio>
<button onclick="playAssistantAudio('Your meeting is at 2 PM')">Play</button>
```

### JavaScript
```javascript
async function playAssistantAudio(text, spokenTime = null) {
    try {
        const response = await fetch('/api/tts', {
            method: 'POST',
            body: JSON.stringify({
                text: text,
                spoken_time: spokenTime,
                voice: getSavedVoice(),
                speed: getSavedSpeed(),
                format: 'wav'
            })
        });
        
        const audio = await response.blob();
        const url = URL.createObjectURL(audio);
        document.getElementById('tts-player').src = url;
        document.getElementById('tts-player').play();
        
    } catch (error) {
        console.error('TTS failed:', error);
        // Show text fallback instead
    }
}
```

---

## Testing Scenarios

### Positive Tests
- [x] Synthesize short text (< 100 chars)
- [x] Synthesize long text (> 500 chars)
- [x] Synthesize with special characters
- [x] Synthesize with numbers/times
- [x] Female voice synthesis
- [x] Male voice synthesis
- [x] Slow/normal/fast speeds
- [x] WAV format output
- [x] Base64 format output
- [x] Cache hit (same text twice)

### Negative Tests
- [x] Empty text
- [x] Text > 1000 chars
- [x] Invalid voice option
- [x] Invalid speed option
- [x] Malformed JSON
- [x] Missing required fields

### Integration Tests
- [x] Coqui failure → gTTS fallback
- [x] Both engines fail → text response
- [x] Concurrent requests handled
- [x] Audio plays in frontend
- [x] Settings persist across requests
