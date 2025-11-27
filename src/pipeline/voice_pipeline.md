# Complete Voice Pipeline Documentation

## Overview
End-to-end voice interaction orchestration: wake word → recording → cleanup → recognition → processing → response → TTS → playback.

## Pipeline Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    VOICE PIPELINE FLOW                       │
└─────────────────────────────────────────────────────────────┘

[1] IDLE STATE
    ↓
Continuous listening for wake word (Porcupine, 0.1% CPU)

[2] WAKE WORD DETECTED
    ├─ Confidence check: > 50%?
    ├─ Yes → Go to [3]
    └─ No → Return to [1]

[3] ACTIVATION
    ├─ Play "beep" sound (100ms)
    ├─ Mic button glows (visual feedback)
    └─ Show: "Listening..."

[4] RECORDING
    ├─ Start audio capture (16kHz, 16-bit mono)
    ├─ Show interim transcription
    ├─ Monitor for silence (1.5 seconds timeout)
    └─ Max recording: 30 seconds

[5] SILENCE DETECTED
    ├─ Stop recording
    └─ Go to [6]

[6] AUDIO CLEANUP
    ├─ Noise reduction (noisereduce library)
    ├─ Silence trimming (pydub)
    ├─ Volume normalization (-20dB target)
    └─ Go to [7]

[7] SPEECH RECOGNITION (STT)
    ├─ Send cleaned audio to Vosk
    ├─ Get transcript + confidence
    ├─ Confidence < 60%?
    │  ├─ Yes: "I didn't catch that. Please repeat." → Go to [4]
    │  └─ No: Go to [8]
    └─ Result: final_transcript

[8] NLU PROCESSING
    ├─ Send transcript to /api/voice_cmd
    ├─ Parse: action, date, time, parameters
    ├─ Route to handler: create_event, get_events, cancel_event
    └─ Get: assistant_text, spoken_time, needs_more_info

[9] EXECUTE ACTION
    ├─ Calendar API call (if applicable)
    ├─ Get result: success/error
    └─ Go to [10]

[10] TTS SYNTHESIS
    ├─ Synthesize assistant_text
    ├─ Use spoken_time for emphasis
    ├─ Select user's voice preference
    ├─ Coqui TTS (primary) or gTTS (fallback)
    └─ Get: audio_file (WAV)

[11] PLAYBACK
    ├─ Play TTS audio
    ├─ Show response bubble (5s auto-hide)
    ├─ Display events (if get_events action)
    └─ Go to [12]

[12] NEXT INTERACTION
    ├─ needs_more_info = true?
    │  ├─ Yes: Go to [4] (re-open mic)
    │  └─ No: Go to [13]
    └─ Reset state

[13] RETURN TO IDLE
    ├─ Hide response bubble
    ├─ Reset UI
    ├─ Resume listening for wake word
    └─ Go to [1]
```

## Detailed Stage Descriptions

### Stage 1: Idle Listening
- **Purpose**: Monitor for wake word activation
- **CPU**: 0.1% (ultra-low power)
- **Duration**: Until wake word detected
- **Action**: Load user's encrypted wake word model at startup
- **Timeout**: None (continuous)

### Stage 2: Wake Word Detection
- **Purpose**: Trigger STT activation
- **Confidence Threshold**: > 50%
- **Engine**: Porcupine
- **Latency**: ~15ms
- **Accuracy**: 99%

**Decision**:
```
IF confidence > 50%:
    Go to Stage 3 (Activation)
ELSE:
    Continue listening (Stage 1)
```

### Stage 3: Activation
- **Duration**: 100ms (instantaneous)
- **Audio**: Play 100ms "beep" at 1000Hz
- **Visual**: Mic button glows (CSS animation)
- **Text**: "Listening..." message appears
- **State Change**: IDLE → TRIGGER_DETECTED → CAPTURING

### Stage 4: Recording
- **Purpose**: Capture user's spoken command
- **Audio Format**: 16kHz, 16-bit mono
- **Duration**: Until silence or 30s max
- **Real-time Feedback**:
  - Show interim transcription every 500ms
  - Show confidence percentage
  - Display noise level indicator

**Silence Detection**:
- Threshold: -40dB
- Duration: 1.5 seconds
- Action: Stop recording, go to Stage 5

**Max Duration**:
- Limit: 30 seconds
- Action: Auto-stop, process partial command

### Stage 5: Silence Detected / Recording Stopped
- **Purpose**: Transition point
- **Duration**: <100ms
- **Action**: Stop audio capture
- **Next**: Go to Stage 6 (cleanup)

### Stage 6: Audio Cleanup Pipeline
Three sub-stages run sequentially:

**6A. Noise Reduction**
- Library: `noisereduce`
- Time: ~40ms
- Method: Learn noise profile from initial silence
- Result: Reduced background noise

**6B. Silence Trimming**
- Library: `pydub`
- Time: ~10ms
- Method: Remove silence before/after speech
- Threshold: -40dB
- Padding: Keep 100ms silence

**6C. Volume Normalization**
- Library: `scipy`
- Time: ~10ms
- Target: -20dB RMS
- Method: Calculate RMS, adjust gain
- Peak limiting: -3dB to prevent clipping

**Output**: Cleaned audio ready for STT

### Stage 7: Speech Recognition (STT)
- **Purpose**: Convert audio to text
- **Engine**: Vosk (offline)
- **Language**: English (en-US)
- **Model Size**: ~50MB (downloaded once)
- **Latency**: ~100-200ms
- **Accuracy**: 85-95% (depends on audio quality)

**Confidence Check**:
```
confidence = STT result confidence (0.0-1.0)

IF confidence >= 0.60:
    Go to Stage 8 (NLU)
ELSE:
    Speak: "I didn't catch that. Please repeat."
    Go to Stage 4 (Re-record)
```

**Failure Handling**:
```
IF STT fails:
    Show: "I couldn't process that audio."
    Return to Stage 1 (idle listening)
```

### Stage 8: Natural Language Understanding (NLU)
- **Purpose**: Extract intent and parameters from transcript
- **Endpoint**: POST /api/voice_cmd
- **Engine**: Hugging Face Mistral API (or fallback keyword matching)
- **Time**: ~1-2 seconds

**Input**:
```python
{
    "transcript": "set a meeting with john tomorrow at 2 PM",
    "user_id": "user_123",
    "context": {}
}
```

**Output**:
```python
{
    "action": "create_event",
    "title": "meeting with john",
    "date": "2025-11-26",
    "time": "14:00",
    "spoken_time": "2 PM",
    "confirm_required": False,
    "assistant_text": "I've scheduled your meeting with John tomorrow at 2 PM",
    "needs_more_info": False
}
```

**Supported Actions**:
- `create_event`: Schedule calendar event
- `get_events`: List events for date
- `cancel_event`: Delete event
- `other`: Unrecognized command

### Stage 9: Execute Action
- **Purpose**: Perform calendar operation
- **Time**: 0.5-2 seconds
- **Endpoint**: Internal Python function call
- **Database**: Google Calendar API

**For create_event**:
```python
calendar_actions.create_event(
    user_id="user_123",
    title="meeting with john",
    date_str="tomorrow",
    time_str="2 PM",
    timezone="America/New_York"
)
```

**Result**:
```python
{
    "success": True,
    "event_id": "abc123",
    "event": {
        "title": "meeting with john",
        "start": "2025-11-26T14:00:00",
        "end": "2025-11-26T15:00:00"
    }
}
```

**Error Handling**:
```python
IF action fails:
    assistant_text = "I couldn't complete that action."
    Skip to Stage 10 (TTS)
    needs_more_info = False
```

### Stage 10: Text-to-Speech (TTS) Synthesis
- **Purpose**: Convert assistant text to natural audio
- **Engine**: Coqui TTS (primary) or gTTS (fallback)
- **Time**: 1-3 seconds
- **Voice**: User's preference (female/male)
- **Speed**: User's preference (slow/normal/fast)

**Emphasis on Spoken Time**:
- Insert slight pause before time phrase
- Use higher pitch for time
- Example: "Your meeting is [PAUSE] at [HIGH PITCH] two PM"

**Input**:
```python
{
    "text": "I've scheduled your meeting with John tomorrow at 2 PM",
    "spoken_time": "2 PM",
    "voice": "female",
    "speed": "normal"
}
```

**Output**:
```python
{
    "success": True,
    "audio_path": "/tmp/tts_abc123.wav",
    "duration_ms": 3200,
    "engine": "coqui"
}
```

**Fallback Chain**:
```
Try Coqui TTS
  ↓ (fails)
Try gTTS
  ↓ (fails)
Return text only (no audio)
```

### Stage 11: Playback & Display
- **Purpose**: Play audio and show results
- **Duration**: 3-5 seconds

**Audio Playback**:
- Use browser `<audio>` element
- Stream from `/tmp/tts_*.wav`
- Enable speaker

**Response Display**:
- Show single bubble with assistant text
- Auto-hide after 5 seconds
- No chat history

**Event Display** (if get_events):
- Show event cards (title, date, time)
- Each card appears 400ms
- Auto-hide all after 5 seconds

### Stage 12: Multi-turn Decision
- **Purpose**: Determine if follow-up needed
- **Flag**: `needs_more_info` from NLU

**Decision**:
```
IF needs_more_info == True:
    Stay in NEEDS_INFO state
    Re-open mic (Stage 4)
    Prompt: "What would you like to add?"
    
ELSE:
    Go to Stage 13 (Idle)
```

### Stage 13: Return to Idle
- **Purpose**: Reset state, resume listening
- **Duration**: Immediate
- **Actions**:
  - Hide response bubble
  - Clear transcript display
  - Clear interim text
  - State: IDLE
  - Resume wake word listening (Stage 1)

## Error Handling & Recovery

### Low-Confidence STT (< 60%)
```
Speak: "I didn't catch that. Please repeat."
Re-open mic (Stage 4)
Max retries: 2
```

### No Audio Detected (Silence from start)
```
Speak: "I didn't hear anything. Please try again."
Return to idle
```

### High Background Noise
```
Speak: "There's too much noise. Can you move to a quieter place?"
Return to idle
```

### NLU Parsing Error
```
Speak: "I didn't understand that. Can you rephrase?"
needs_more_info = True
Re-open mic
```

### Calendar API Fails
```
Speak: "I couldn't access your calendar. Please try again."
Return to idle
Error logged to logs/voice.log
```

### TTS Synthesis Fails
```
Show response text instead
Don't speak (user reads text)
Return to idle
```

### Complete Pipeline Failure
```
Return to idle
Log error
Show notification: "Something went wrong. Please try again."
```

## Safety Rules (See speech_rules.md)

### Accidental Wake Word Detection
- **Rule**: Require 1 second silence before recording starts
- **Reason**: Prevent random words triggering STT
- **Implementation**: Silence timer after wake detection

### User Says "Stop" or "Cancel"
- **Rule**: Immediately stop all processing
- **Actions**:
  - Pause TTS playback
  - Stop recording
  - Close mic
  - Clear transcript
  - Return to idle
- **Hotkey**: Keyboard 'S' key (during recording)

### User Interrupts Mid-Response
- **Rule**: Stop TTS, clear bubble, re-open mic
- **Trigger**: User starts speaking during playback
- **Implementation**: Voice activation detector

## Configuration Files

**See these for tuning**:
- `src/stt/mic_settings.json` - STT parameters
- `src/tts/voice_settings.json` - TTS parameters
- `src/wakeword/wakeword_settings.json` - Wake word settings
- `src/audio_processing/cleanup_pipeline.md` - Cleanup thresholds

## Performance Metrics

### Timeline (Happy Path)
```
Stage 1: Idle listening        → 0ms (background)
Stage 2: Wake detection        → 15ms
Stage 3: Activation            → 100ms
Stage 4: Recording             → 3-5 seconds (user speaks)
Stage 5: Stop recording        → 50ms
Stage 6: Audio cleanup         → 85ms
Stage 7: STT recognition       → 100-200ms
Stage 8: NLU processing        → 1-2 seconds
Stage 9: Execute action        → 0.5-2 seconds
Stage 10: TTS synthesis        → 1-3 seconds
Stage 11: Playback            → 3-5 seconds
Stage 13: Return to idle       → 100ms

TOTAL END-TO-END: 10-20 seconds
User perceives: "I said command" → "Heard response" (5s)
```

### Resource Usage
```
Wake listening:     0.1% CPU, 30MB RAM
Recording:          1% CPU, 5MB RAM
Cleanup:            15% CPU, 10MB RAM
STT recognition:    25% CPU, 100MB RAM
NLU processing:     10% CPU, 50MB RAM
TTS synthesis:      30% CPU, 100MB RAM
Peak memory:        ~150MB
```

## Testing Pipeline

### Unit Tests
- [x] Each stage independently
- [x] Wake word detection accuracy
- [x] Audio cleanup effectiveness
- [x] STT accuracy on various audio types
- [x] NLU action extraction
- [x] Calendar action execution
- [x] TTS audio generation

### Integration Tests
- [x] Full pipeline: wake → recognize → respond
- [x] Multi-turn interaction
- [x] Error recovery at each stage
- [x] Concurrent operations
- [x] Timeout handling

### End-to-End Tests
- [x] Real user scenario: "Set meeting tomorrow 2 PM"
- [x] Complex scenario with multi-turn: "Set a meeting" → "with John" → "at 2 PM"
- [x] Error scenario: No audio → Silence detected → Noise interference
- [x] Stress test: Rapid commands (10+ per minute)

### Manual Testing Checklist
- [ ] Wake word detected from 1m away
- [ ] Command recognized in noisy environment
- [ ] Calendar event created with correct time
- [ ] Multi-turn flow works smoothly
- [ ] TTS sounds natural and clear
- [ ] Silence timeout works (1.5 seconds)
- [ ] User interruption handled (Ctrl+S stops TTS)
- [ ] Error messages are helpful
- [ ] Audio quality improves with cleanup

## Future Enhancements

1. **Streaming STT**: Don't wait for silence, stream recognition as speaking
2. **Streaming TTS**: Start playback before full synthesis completes
3. **Context Awareness**: Remember previous commands in session
4. **Emotion Detection**: Detect frustration, adjust response tone
5. **Predictive Actions**: Pre-fill common patterns (recurring meetings)
6. **Custom Workflows**: User-defined multi-step sequences
