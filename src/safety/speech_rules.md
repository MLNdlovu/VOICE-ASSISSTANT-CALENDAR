# Safety Rules & Error Handling Documentation

## Overview
Critical safety rules and error handling procedures for voice pipeline.

## Safety Rule 1: Accidental Wake Word Detection

### Problem
User says sentence containing words similar to wake phrase → Accidental STT activation

**Example**:
```
Wake word: "Hey Calendar"
User says: "Hey, are you available next Monday?"
Risk: "Hey" alone might trigger STT
```

### Solution: 1-Second Silence Before Recording

**Implementation**:
```python
def on_wake_word_detected():
    # Wake word matched
    play_beep()
    
    # Wait 1 second of silence before recording
    silence_start = time.time()
    
    while time.time() - silence_start < 1.0:
        # Monitor audio level
        audio_chunk = get_audio_chunk()
        volume_db = calculate_volume(audio_chunk)
        
        if volume_db > -40:  # Speech detected
            silence_start = time.time()  # Reset counter
        
        if timeout > 2.0:  # No silence for 2 seconds
            return_to_idle()  # False positive
    
    # 1 second silence confirmed → Start recording
    start_recording()
```

**Behavior**:
- Beep sounds immediately (feedback)
- Wait 1 second of quiet before recording starts
- If user speaks during 1-second wait → Reset timer
- If 2+ seconds without silence → Return to idle
- User hears this as: Beep → brief pause → "Listening..."

**Result**: Only genuine commands recorded, accidental phrases ignored

---

## Safety Rule 2: User Says "Stop" or "Cancel"

### Problem
User wants to interrupt command execution at any point

### Solution: Voice + Keyboard Fallback

**Voice Interruption**:
```python
# If user says "stop", "cancel", "never mind", etc.
STOP_PHRASES = ["stop", "cancel", "never mind", "dismiss", "quit"]

def on_transcript_received(transcript):
    if any(word in transcript.lower() for word in STOP_PHRASES):
        handle_stop_command()
```

**Keyboard Fallback**:
```javascript
// Press 'S' during recording to stop
document.addEventListener('keydown', (e) => {
    if (e.key.toLowerCase() === 's' && recordingActive) {
        stopRecording();
        returnToIdle();
        console.log('Recording stopped by user');
    }
});
```

**What "Stop" Does**:
```
1. Stop current recording immediately
2. Stop TTS playback (if playing)
3. Clear transcript display
4. Clear response bubble
5. Return to idle listening state
6. Beep twice to confirm stop
```

**State Machine**:
```
ANY STATE (Recording/Processing/Playing)
    ↓ (User says "stop")
Return to IDLE
    ↓
Resume wake word listening
```

---

## Safety Rule 3: Unintelligible Speech (Low Confidence)

### Problem
User speaks unclearly → STT confidence < 60%

### Solution: Polite Retry Loop

**Implementation**:
```python
def on_speech_recognized(transcript, confidence):
    if confidence < 0.60:
        # Low confidence
        speak("I didn't catch that clearly. Could you please repeat?")
        retry_count += 1
        
        if retry_count <= 2:
            # Re-open mic for new attempt
            go_to_recording_stage()
        else:
            # Max retries reached
            speak("I'm having trouble understanding. Please try again later.")
            return_to_idle()
```

**User Experience**:
1. User speaks unclearly
2. Assistant: "I didn't catch that. Could you please repeat?"
3. Mic stays open, user speaks again
4. After 2 failed attempts: Return to idle

**Confidence Thresholds**:
```
confidence >= 0.85: Perfect match, proceed
confidence >= 0.60: Good enough, proceed
confidence < 0.60:  Ask for repeat
```

---

## Safety Rule 4: No Audio Detected (Complete Silence)

### Problem
User doesn't speak after activation → Silence throughout recording

### Solution: Timeout with Gentle Notification

**Implementation**:
```python
def recording_timeout():
    # No speech detected after 10 seconds of recording
    speak("I didn't hear anything. Please try again.")
    return_to_idle()

def silence_timeout():
    # 1.5 seconds of silence detected
    stop_recording()
    process_audio()
```

**Timeline**:
```
0s:   Wake word detected → beep → "Listening..."
0-10s: Recording phase (waiting for speech)
10s:  No audio detected → "I didn't hear anything"
0-1.5s: Speech detected, user pauses
1.5s: Silence timeout → Stop recording, process
```

---

## Safety Rule 5: High Background Noise Detection

### Problem
User in loud environment (café, traffic) → Recognition will fail

### Solution: Pre-emptive Noise Warning

**Implementation**:
```python
def on_recording_start():
    # Analyze first 500ms for noise level
    noise_level = analyze_ambient_noise()
    
    if noise_level > -20:  # Very loud
        speak("There's quite a bit of noise. Can you move to a quieter place?")
        pause_recording = True
        return_to_idle()
    elif noise_level > -28:  # Moderate noise
        speak("There's some background noise, but I'll do my best.")
        continue_recording()
    else:  # Quiet environment
        continue_recording()
```

**Noise Classification**:
```
dB > -10:   Very loud (stop recording)
dB -10 to -20:  Loud (warn, continue with caution)
dB -20 to -35:  Moderate (normal processing)
dB -35 to -50:  Quiet (ideal conditions)
dB < -50:   Silent (no audio)
```

---

## Safety Rule 6: Calendar API Failure

### Problem
Google Calendar API unavailable → Event creation fails

### Solution: User-Friendly Fallback

**Implementation**:
```python
def create_calendar_event():
    try:
        result = calendar_api.create_event(...)
        if result.success:
            speak(f"Event created: {result.title}")
            return result
    except CalendarAPI.Error as e:
        # API failed
        log_error(e)
        
        # Notify user
        speak("I couldn't access your calendar. Please check your connection and try again.")
        
        return {
            "success": False,
            "error": "calendar_unavailable",
            "fallback": "Visit calendar.google.com to add manually"
        }
```

**User Flow**:
1. User: "Set a meeting tomorrow at 2 PM"
2. Assistant: "I couldn't access your calendar. Please check your connection..."
3. User redirected to manual calendar entry

---

## Safety Rule 7: STT Model Not Downloaded

### Problem
App starts → Vosk model not in `/models/vosk_en/` → STT unavailable

### Solution: Auto-Download + Fallback

**Implementation**:
```python
def initialize_stt_engine():
    if not model_exists('/models/vosk_en/'):
        # Model missing
        download_vosk_model()  # ~50MB, takes 45 seconds
        
        if download_failed():
            # Fallback: Disable voice features
            voice_disabled = True
            show_keyboard_only_mode()
            speak("Voice features are loading. Use keyboard for now.")
```

**User Experience**:
1. First app load: "Downloading speech model (45/50 MB)..."
2. Progress bar shows download status
3. Once complete: Voice features enabled
4. Subsequent loads: Instant voice available

---

## Safety Rule 8: TTS Synthesis Failure

### Problem
Coqui TTS unavailable → gTTS unavailable → No audio generation

### Solution: Graceful Text-Only Fallback

**Implementation**:
```python
def synthesize_response(text):
    try:
        # Try Coqui TTS
        audio = coqui_tts.synthesize(text)
        if audio:
            return audio
    except:
        pass
    
    try:
        # Try gTTS fallback
        audio = gtts.synthesize(text)
        if audio:
            return audio
    except:
        pass
    
    # Both failed → Return text
    return {
        "success": False,
        "audio": None,
        "text": text,
        "fallback": "text_only"
    }
```

**User Experience**:
```
TTS Success: Hear audio response ✓
gTTS Fallback: Hear slightly robotic audio
Text Fallback: Read response on screen
```

---

## Safety Rule 9: Microphone Permission Denied

### Problem
Browser microphone permission denied → Can't record audio

### Solution: Clear Permission Request + Fallback

**Implementation (JavaScript)**:
```javascript
async function requestMicrophonePermission() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: true
        });
        // Permission granted
        initializeAudioCapture(stream);
        
    } catch (error) {
        if (error.name === 'NotAllowedError') {
            // User denied permission
            showPermissionRequest();
            speak("Please allow microphone access in your browser settings");
            voice_disabled = true;
        } else if (error.name === 'NotFoundError') {
            // No microphone device
            showError("No microphone found. Please connect a microphone.");
        }
    }
}
```

**Recovery**:
1. Show permission request modal
2. Explain why microphone needed
3. Direct user to browser settings
4. Enable keyboard-only fallback
5. Re-ask for permission on page reload

---

## Safety Rule 10: Multi-Turn Timeout

### Problem
User starts multi-turn flow → Doesn't continue → Mic left open

### Solution: Auto-Timeout After Inactivity

**Implementation**:
```python
def on_needs_more_info():
    speak("What else would you like to add?")
    activity_timeout = 30  # 30 seconds
    
    while activity_timeout > 0:
        if user_speaks():
            activity_timeout = 30  # Reset
        else:
            activity_timeout -= 1
    
    # Timeout reached
    speak("I'm closing this request. Try again when ready.")
    return_to_idle()
```

**Timeline**:
```
"What else would you like to add?" → Mic open
0-30s: Waiting for user input
30s: Timeout, close mic, return to idle
If user speaks: Reset timer
```

---

## Safety Rule 11: Duplicate Command Prevention

### Problem
User speaks once → Processed twice (network retry)

### Solution: Deduplication with Request ID

**Implementation**:
```python
@app.route('/api/voice_cmd', methods=['POST'])
def voice_command():
    request_id = request.json.get('request_id')
    
    # Check if we've processed this request
    if is_duplicate_request(request_id):
        # Return cached response
        return get_cached_response(request_id)
    
    # Process new request
    result = process_transcript(...)
    
    # Cache result
    cache_response(request_id, result, ttl=5)
    
    return result
```

**Frontend**:
```javascript
const requestId = generateUUID();

const response = await fetch('/api/voice_cmd', {
    method: 'POST',
    body: JSON.stringify({
        transcript: "set a meeting",
        request_id: requestId  // Unique ID
    })
});
```

---

## Safety Rule 12: Session Privacy Cleanup

### Problem
User closes browser → Voice data left in memory/cache

### Solution: Auto-Clear on Page Unload

**Implementation (JavaScript)**:
```javascript
window.addEventListener('beforeunload', () => {
    // Clear sensitive data
    sessionStorage.clear();
    localStorage.removeItem('pending_transcript');
    localStorage.removeItem('last_command');
    
    // Stop recording if active
    if (recordingActive) {
        stopRecording();
    }
    
    // Stop TTS if playing
    if (ttsPlaying) {
        stopTTS();
    }
});
```

**On Tab Close**:
1. Clear sessionStorage (trigger phrase)
2. Stop all audio processing
3. Close microphone
4. Clear transcript
5. Delete temporary files

---

## Error Recovery Matrix

| Stage | Error | Symptom | Recovery | User Message |
|---|---|---|---|---|
| Wake | Confidence < 50% | Accidental activation | Require 1s silence | (beep, brief pause) |
| Recording | No audio | Silence timeout | Return to idle | "I didn't hear anything" |
| Recording | High noise | Bad recognition | Warn, ask to move | "There's too much noise" |
| STT | Confidence < 60% | Unclear text | Ask for repeat (2x) | "I didn't catch that" |
| STT | Timeout | No response (30s) | Return to idle | (timeout) |
| NLU | Parse error | Unrecognized action | Ask for rephrase | "I didn't understand that" |
| Action | API fails | Calendar unavailable | Show text fallback | "I couldn't access calendar" |
| TTS | Coqui fails | No audio | Try gTTS | (robotic voice) |
| TTS | All fail | No audio | Show text only | (text in bubble) |
| Pipeline | Complete failure | All systems down | Keyboard-only mode | "Voice unavailable" |

---

## Testing Safety Rules

### Unit Tests
- [x] Silence detection threshold
- [x] Noise classification accuracy
- [x] Confidence scoring
- [x] Timeout calculations
- [x] Error message selection

### Integration Tests
- [x] Full error scenario: noise → ask to move → proceed
- [x] Low confidence → retry → success
- [x] Stop command during recording
- [x] Stop command during playback
- [x] Multi-turn timeout

### Manual Tests
- [ ] Test in quiet room
- [ ] Test in loud café
- [ ] Test with low microphone volume
- [ ] Test with headphones
- [ ] Test permission denial
- [ ] Test model not found on first run
- [ ] Test network timeout scenario
- [ ] Test saying "stop" at each stage

---

## Monitoring & Logging

### Events Logged to `logs/voice.log`
```
[2025-11-25 10:30:45] INFO: Wake word detected (confidence: 0.98)
[2025-11-25 10:30:47] INFO: Recording started
[2025-11-25 10:30:51] INFO: Silence detected, processing audio
[2025-11-25 10:30:52] INFO: STT result: "set a meeting tomorrow at 2 PM" (confidence: 0.89)
[2025-11-25 10:30:53] INFO: NLU: action=create_event, date=2025-11-26, time=14:00
[2025-11-25 10:30:54] INFO: Calendar event created: event_id=abc123
[2025-11-25 10:30:55] INFO: TTS synthesis: Coqui engine, duration=2.1s
[2025-11-25 10:30:57] INFO: Response played, returning to idle

[2025-11-25 10:35:20] WARN: Low STT confidence (0.45), asking for repeat
[2025-11-25 10:35:25] ERROR: Calendar API timeout after 10s
[2025-11-25 10:35:26] ERROR: TTS synthesis failed, using text fallback
```

### Metrics Tracked
- Wake word detection rate
- False positive rate
- STT confidence average
- NLU success rate
- Action execution success rate
- Error rate by type
- Average response time (end-to-end)
