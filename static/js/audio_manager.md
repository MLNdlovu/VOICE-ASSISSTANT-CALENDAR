# Frontend Audio Manager Documentation

## Overview
JavaScript module managing all audio I/O: microphone input, TTS playback, beep/chime sounds.

## File Structure

```html
<!-- Audio Players -->
<audio id="tts-player" preload="none"></audio>
<audio id="beep-sound" preload="auto">
    <source src="/static/sounds/beep.mp3" type="audio/mpeg">
</audio>
<audio id="chime-sound" preload="auto">
    <source src="/static/sounds/chime.mp3" type="audio/mpeg">
</audio>
<audio id="error-sound" preload="auto">
    <source src="/static/sounds/error.mp3" type="audio/mpeg">
</audio>
```

## Core Functions

### `initializeAudioManager()`
**Purpose**: Setup audio on app start
**Returns**:
```python
{
    "microphone": "ready",
    "speakers": "ready",
    "permissions": "granted",
    "sample_rate": 16000
}
```

**Actions**:
1. Check microphone permission
2. Initialize Web Audio API
3. Load sound effects
4. Setup event listeners

---

### `playAssistantAudio(text, spokenTime)`
**Purpose**: Synthesize and play TTS
**Parameters**:
- `text` (str): What to speak
- `spokenTime` (str, optional): Time to emphasize

**Implementation**:
```javascript
async function playAssistantAudio(text, spokenTime = null) {
    try {
        const response = await fetch('/api/tts', {
            method: 'POST',
            body: JSON.stringify({
                text: text,
                spoken_time: spokenTime,
                voice: getSavedVoice() || 'female',
                speed: getSavedSpeed() || 'normal',
                format: 'wav'
            })
        });
        
        if (!response.ok) {
            console.error('TTS failed:', response.status);
            return;
        }
        
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        
        const player = document.getElementById('tts-player');
        player.src = audioUrl;
        player.play();
        
        // UI cleanup on end
        player.onended = () => {
            URL.revokeObjectURL(audioUrl);
            hideBubble();
        };
        
    } catch (error) {
        console.error('Audio playback failed:', error);
        // Fallback: show text only
        showTextBubble(text);
    }
}
```

**Flow**:
1. Send text to `/api/tts`
2. Receive WAV audio blob
3. Create object URL
4. Set as audio src
5. Play audio
6. Clean up on finish

---

### `playBeepSound()`
**Purpose**: Play activation beep (100ms, 1000Hz)
**Usage**: Feedback when wake word detected

```javascript
function playBeepSound() {
    const beep = document.getElementById('beep-sound');
    beep.currentTime = 0;
    beep.volume = 0.7;
    beep.play();
}
```

**When Used**:
- Wake word detected
- Recording started
- User permission requested

---

### `playChimeSound()`
**Purpose**: Play pleasant chime (success sound)
**Usage**: Feedback when command completed successfully

```javascript
function playChimeSound() {
    const chime = document.getElementById('chime-sound');
    chime.currentTime = 0;
    chime.volume = 0.5;
    chime.play();
}
```

**When Used**:
- Event created successfully
- Event cancelled successfully
- Settings saved

---

### `playErrorSound()`
**Purpose**: Play error buzzer (short buzz)
**Usage**: Feedback when command fails

```javascript
function playErrorSound() {
    const error = document.getElementById('error-sound');
    error.currentTime = 0;
    error.volume = 0.6;
    error.play();
}
```

**When Used**:
- STT recognition failed
- Calendar API error
- Network timeout

---

### `startMicrophoneCapture()`
**Purpose**: Access microphone and start recording
**Returns**:
```python
{
    "status": "recording",
    "sample_rate": 16000,
    "channels": 1
}
```

**Implementation**:
```javascript
async function startMicrophoneCapture() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                sampleRate: 16000,
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: false  // We'll normalize ourselves
            }
        });
        
        // Create audio context
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const mediaStreamSource = audioContext.createMediaStreamSource(stream);
        const processor = audioContext.createScriptProcessor(4096, 1, 1);
        
        mediaStreamSource.connect(processor);
        processor.connect(audioContext.destination);
        
        // Process audio chunks
        processor.onaudioprocess = (event) => {
            const audioData = event.inputBuffer.getChannelData(0);
            sendAudioChunk(audioData);
        };
        
        recordingActive = true;
        return { status: 'recording' };
        
    } catch (error) {
        if (error.name === 'NotAllowedError') {
            showPermissionRequest();
            speak("Please allow microphone access");
        } else if (error.name === 'NotFoundError') {
            showError("No microphone found");
        }
        return { status: 'error', error: error.message };
    }
}
```

---

### `stopMicrophoneCapture()`
**Purpose**: Stop recording and return audio buffer
**Returns**:
```python
{
    "status": "stopped",
    "audio_buffer": bytes,
    "duration_ms": 4500
}
```

```javascript
function stopMicrophoneCapture() {
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }
    
    recordingActive = false;
    
    return {
        status: 'stopped',
        audio_buffer: audioBuffer,
        duration_ms: audioBuffer.length / 16  // at 16kHz
    };
}
```

---

### `sendAudioChunk(audioData)`
**Purpose**: Send audio in real-time to backend for STT processing
**Parameters**:
- `audioData` (Float32Array): Audio chunk (4096 samples)

```javascript
async function sendAudioChunk(audioData) {
    if (!recordingActive) return;
    
    // Convert Float32 to Int16
    const int16Data = float32ToInt16(audioData);
    
    // Send chunk
    try {
        const response = await fetch('/api/stt/chunk', {
            method: 'POST',
            headers: { 'Content-Type': 'application/octet-stream' },
            body: int16Data
        });
        
        const result = await response.json();
        
        if (result.is_final) {
            // Final result
            onFinalTranscript(result.text);
        } else if (result.text) {
            // Interim result
            updateInterimTranscript(result.text);
        }
        
    } catch (error) {
        console.error('Audio send failed:', error);
    }
}
```

---

### `requestMicrophonePermission()`
**Purpose**: Explicitly request microphone access
**Shows**: Browser permission dialog

```javascript
async function requestMicrophonePermission() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        // Permission granted
        stream.getTracks().forEach(track => track.stop());
        return { granted: true };
    } catch (error) {
        return { granted: false, error: error.message };
    }
}
```

---

### `setMicrophoneVolume(volume)`
**Purpose**: Adjust mic input gain
**Parameters**:
- `volume` (0.0-1.0): Input level multiplier

```javascript
function setMicrophoneVolume(volume) {
    if (gainNode) {
        gainNode.gain.value = volume;
    }
    localStorage.setItem('mic_volume', volume);
}
```

---

### `setTTSVolume(volume)`
**Purpose**: Adjust TTS playback volume
**Parameters**:
- `volume` (0.0-1.0): Output level

```javascript
function setTTSVolume(volume) {
    const player = document.getElementById('tts-player');
    player.volume = volume;
    localStorage.setItem('tts_volume', volume);
}
```

---

### `getSpeakerAvailable()`
**Purpose**: Check if speakers available and working
**Returns**:
```python
{
    "available": True,
    "devices": [
        "Built-in Speaker",
        "Headphones"
    ],
    "current_device": "Built-in Speaker"
}
```

```javascript
async function getSpeakerAvailable() {
    try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const audioOutputs = devices.filter(d => d.kind === 'audiooutput');
        
        return {
            available: audioOutputs.length > 0,
            devices: audioOutputs.map(d => d.label),
            current_device: audioOutputs[0]?.label || 'Default'
        };
    } catch (error) {
        return { available: false, error: error.message };
    }
}
```

---

### `setSinkId(deviceId)`
**Purpose**: Switch audio output device (speaker/headphones)
**Parameters**:
- `deviceId` (str): Device ID from getSpeakerAvailable()

```javascript
async function setSinkId(deviceId) {
    try {
        const audio = document.getElementById('tts-player');
        await audio.setSinkId(deviceId);
        localStorage.setItem('speaker_device', deviceId);
        return { success: true };
    } catch (error) {
        return { success: false, error: error.message };
    }
}
```

---

## HTML Audio Elements

```html
<!-- TTS Playback -->
<audio id="tts-player" 
    preload="none"
    style="display: none;">
</audio>

<!-- Beep Sound (Wake Word Detected) -->
<audio id="beep-sound" 
    preload="auto"
    style="display: none;">
    <source src="/static/sounds/beep.mp3" type="audio/mpeg">
</audio>

<!-- Chime Sound (Success) -->
<audio id="chime-sound"
    preload="auto"
    style="display: none;">
    <source src="/static/sounds/chime.mp3" type="audio/mpeg">
</audio>

<!-- Error Sound (Failure) -->
<audio id="error-sound"
    preload="auto"
    style="display: none;">
    <source src="/static/sounds/error.mp3" type="audio/mpeg">
</audio>
```

---

## Sound Files

**Create and place these in `/static/sounds/`**:

### beep.mp3
- Frequency: 1000 Hz
- Duration: 100ms
- Purpose: Wake word detected
- Tools: Use `ffmpeg` or online tone generator

```bash
ffmpeg -f lavfi -i sine=1000:d=0.1 -q:a 9 -acodec libmp3lame -ab 128k beep.mp3
```

### chime.mp3
- Frequency: 880-1000 Hz ascending
- Duration: 300ms
- Purpose: Success feedback
- Sound: Pleasant ascending chime

### error.mp3
- Frequency: 400-200 Hz descending
- Duration: 200ms
- Purpose: Error feedback
- Sound: Short descending buzz

---

## Volume Levels

```
TTS Speech:      0.7 (clear, natural)
Beep (wake):     0.7 (attention-getting)
Chime (success): 0.5 (pleasant)
Error (buzz):    0.6 (noticeable)
Mic monitoring:  0.0 (silent, no feedback loop)
```

---

## Browser Compatibility

| Feature | Chrome | Firefox | Safari | Edge |
|---|---|---|---|---|
| getUserMedia | ✅ | ✅ | ✅ | ✅ |
| Web Audio API | ✅ | ✅ | ✅ | ✅ |
| AudioContext | ✅ | ✅ | ✅ | ✅ |
| setSinkId | ✅ | ❌ | ✅ | ✅ |
| Blob Audio | ✅ | ✅ | ✅ | ✅ |

---

## Error Handling

### Microphone Not Available
```javascript
catch (error) {
    if (error.name === 'NotFoundError') {
        showError('No microphone found. Please connect one.');
    }
}
```

### Permission Denied
```javascript
catch (error) {
    if (error.name === 'NotAllowedError') {
        showPermissionRequest('Allow microphone access in browser settings');
    }
}
```

### Audio Playback Failed
```javascript
try {
    player.play();
} catch (error) {
    // Show text fallback
    showTextBubble(text);
}
```

---

## Testing Checklist

- [ ] Microphone permission request shows
- [ ] Audio recording works on first try
- [ ] TTS audio plays through speakers
- [ ] Beep sound plays on wake detection
- [ ] Chime sound plays on success
- [ ] Error sound plays on failure
- [ ] Volume controls work
- [ ] Device switching works (if supported)
- [ ] Audio stops on page unload
- [ ] No audio feedback loop (mic echo)
- [ ] Works with headphones
- [ ] Works with external speakers
- [ ] Works in background tab (if permitted)

---

## Security Considerations

### Microphone Permission
- ✅ Request explicitly (not silent)
- ✅ Show why microphone needed
- ✅ Allow user to revoke
- ✅ Don't store audio recordings

### Audio Processing
- ✅ Process audio in-memory
- ✅ Delete buffers after use
- ✅ Never send raw audio to third parties
- ✅ Use HTTPS for audio transmission

### Permissions Reset
- ✅ On page unload: close streams
- ✅ On logout: stop recording
- ✅ Clear buffers on errors
