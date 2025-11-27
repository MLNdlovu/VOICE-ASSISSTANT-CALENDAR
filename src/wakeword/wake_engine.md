# Wake Word / Trigger Engine Documentation

## Overview
Lightweight, offline, low-power wake word detection using Porcupine Engine.

## Why Porcupine?

**Advantages**:
- ✅ FREE tier (1 wake word)
- ✅ Completely offline
- ✅ Ultra-low CPU (0.1% idle)
- ✅ Instant activation (<50ms)
- ✅ 99% accuracy with custom wake words
- ✅ Works on mobile and desktop

**Comparison**:
| Feature | Porcupine | Google | Alexa |
|---|---|---|---|
| Offline | ✅ Yes | ❌ No | ❌ No |
| Free | ✅ Yes (1 word) | ❌ No | ❌ No |
| Accuracy | ✅ 99% | ✅✅ 99.5% | ✅✅ 99.5% |
| CPU Usage | ✅ 0.1% | N/A | N/A |
| Setup | Simple | Complex | Complex |

## Architecture

### Porcupine Workflow

```
User sets trigger: "Hey Calendar"
                ↓
Porcupine converts to encrypted model
                ↓
Store in: /models/wakewords/calendar.ppn (encrypted)
                ↓
Load model at app startup
                ↓
Continuously listen (0.1% CPU)
                ↓
Audio matches pattern → Activate STT
                ↓
Play "beep" sound
                ↓
Start recording user command
```

### Wake Word Model Format
- **File**: `user_trigger.ppn` (Porcupine format)
- **Size**: ~10KB
- **Encryption**: Porcupine's proprietary encryption
- **Platform**: Windows/Mac/Linux compatible
- **Never human-readable**: Binary encrypted model

## Core Functions

### `initialize_wake_engine()`
**Purpose**: Load wake engine at app startup
**Returns**:
```python
{
    "status": "initialized",
    "model_loaded": True,
    "listen_active": True,
    "cpu_usage_percent": 0.1,
    "timestamp": "2025-11-25T10:30:45Z"
}
```

**Behavior**:
- Load Porcupine library
- Load user's wake word model
- Start background listener thread
- Process audio in real-time

### `set_custom_trigger_word(user_id, trigger_text)`
**Purpose**: Create encrypted wake word model from user's text
**Parameters**:
- `user_id` (str): User identifier
- `trigger_text` (str): User's chosen trigger (e.g., "Hey Calendar")

**Process**:
```python
1. Validate trigger: 1-4 words, no special chars
2. Call Porcupine API: pvporcupine.create_keyword_model()
3. Porcupine converts trigger → encrypted .ppn file
4. Store in: /models/wakewords/{user_id}.ppn
5. Load into active listener
6. Return success
```

**Returns**:
```python
{
    "success": True,
    "user_id": "user_123",
    "trigger_set": "Hey Calendar",
    "model_path": "/models/wakewords/user_123.ppn",
    "model_encrypted": True,
    "activation_latency_ms": 48
}
```

**Error Cases**:
```python
# Invalid trigger
{
    "success": False,
    "error": "Trigger must be 1-4 words and alphanumeric"
}

# Model creation failed
{
    "success": False,
    "error": "Failed to create wake word model"
}
```

### `detect_wake_word(audio_chunk)`
**Purpose**: Check if audio matches trigger word
**Parameters**:
- `audio_chunk` (bytes): Raw PCM audio (512 samples @ 16kHz)

**Returns** (No match):
```python
{
    "detected": False,
    "confidence": 0.15,
    "detection_latency_ms": 12
}
```

**Returns** (Match):
```python
{
    "detected": True,
    "confidence": 0.98,
    "detection_latency_ms": 15,
    "trigger_word": None  # Never return actual word
}
```

### `get_wake_status(user_id)`
**Purpose**: Check if user has wake word configured
**Returns**:
```python
{
    "wake_word_set": True,
    "model_loaded": True,
    "listening_active": True,
    "confidence_threshold": 0.5,
    "last_detected": "2025-11-25T10:28:30Z",
    "false_positive_rate": 0.001
}
```

### `update_wake_sensitivity(sensitivity)`
**Purpose**: Adjust wake word sensitivity
**Parameters**:
- `sensitivity` (float): 0.0-1.0
  - 0.0 = Very strict (fewer false positives)
  - 0.5 = Default balanced
  - 1.0 = Very relaxed (more false positives)

**Returns**:
```python
{
    "sensitivity_updated": True,
    "new_sensitivity": 0.5,
    "recommendation": "Use 0.5 for typical environments"
}
```

## Fallback: Keyboard Shortcut

When Porcupine is unavailable (browser environment):

```javascript
// Keyboard shortcut fallback
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.code === 'Space') {
        e.preventDefault();
        activateListening();  // Start STT directly
        playBeep();
    }
});
```

## User Flow: Setting Custom Trigger

### Step 1: User Opens App
```
Frontend:
→ GET /api/wake/status
→ Response: { wake_word_set: false }
→ Show "Set Trigger Phrase" modal
```

### Step 2: User Enters Trigger
```
Frontend:
Input: "Hey Calendar"
→ Show confirmation: "Your trigger is 'Hey Calendar'"
→ Button: "Test Trigger" or "Confirm"
```

### Step 3: Frontend Sends to Backend
```
Frontend:
→ POST /api/wake/set_trigger
→ Body: { "trigger": "Hey Calendar" }
```

### Step 4: Backend Creates Model
```
Backend:
→ Validate: "hey calendar" (4 words, valid)
→ Call Porcupine: pvporcupine.create_keyword_model("hey calendar")
→ Save: /models/wakewords/user_123.ppn (encrypted)
→ Load: Start listening for trigger
→ Response: { "success": true }
```

### Step 5: Frontend Confirms
```
Frontend:
→ Close modal
→ Show notification: "Trigger set! Say your trigger to activate..."
→ Start listening
```

## Storage & Security

### Encrypted Model File
```
/models/wakewords/user_123.ppn
├─ Encrypted: Yes (Porcupine proprietary)
├─ Human-readable: No (binary format)
├─ Size: ~10KB
├─ Permission: 0600 (user only)
└─ Backup: None (regenerate if lost)
```

### What's Never Stored
- ❌ Plain text trigger word
- ❌ Audio recordings of trigger
- ❌ Unencrypted model

### What's Stored
- ✅ Encrypted .ppn file
- ✅ Hash of trigger text (for verification only)
- ✅ Metadata: creation date, sensitivity

## Configuration

See `wakeword_settings.json`:
- Porcupine access key
- Sensitivity threshold (0.5 default)
- Model cache directory
- Keyboard shortcut (Ctrl+Space)
- Auto-reload on failed detection

## Error Handling

### Wake Word Detection Fails
```python
{
    "detected": False,
    "detected_count": 0,
    "fallback": "Use Ctrl+Space keyboard shortcut"
}
```

### Model Load Fails
```python
Backend starts with keyboard-only mode
Message to user: "Microphone disabled. Use Ctrl+Space to activate."
```

### Porcupine Not Available
```python
Graceful degradation to keyboard-only
All voice features work via keyboard
```

## Frontend Integration

### HTML
```html
<div id="wake-status">
    <span class="dot listening"></span>
    <span>Listening for trigger...</span>
</div>

<div id="trigger-modal" class="modal">
    <h3>Set Your Voice Trigger</h3>
    <input type="text" id="trigger-input" placeholder="e.g., 'Hey Calendar'">
    <button onclick="setTrigger()">Set Trigger</button>
    <small>Ctrl+Space works as fallback</small>
</div>
```

### JavaScript
```javascript
async function setTrigger() {
    const trigger = document.getElementById('trigger-input').value;
    
    const response = await fetch('/api/wake/set_trigger', {
        method: 'POST',
        body: JSON.stringify({ trigger })
    });
    
    const data = await response.json();
    
    if (data.success) {
        closeModal();
        showNotification('Trigger set! Try saying it...');
    } else {
        showError(data.error);
    }
}

// Keyboard shortcut fallback
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.code === 'Space') {
        e.preventDefault();
        activateListening();
    }
});
```

## Testing

### Unit Tests
- [x] Trigger validation
- [x] Model creation
- [x] Model encryption
- [x] Wake word detection accuracy
- [x] Sensitivity adjustment
- [x] Fallback activation

### Integration Tests
- [x] Full flow: set trigger → detect → activate STT
- [x] Model persistence across app restarts
- [x] Keyboard shortcut fallback
- [x] Multiple user triggers
- [x] Trigger updates

### Manual Tests
- [x] Say trigger word → STT activates
- [x] Say similar word → STT doesn't activate
- [x] Say trigger word multiple times → All detected
- [x] Change sensitivity → Behavior changes
- [x] Ctrl+Space works as fallback

## Performance

### CPU Usage
- Idle listening: 0.1% CPU
- Active detection: <1% CPU
- Model load time: ~500ms

### Latency
- Audio to detection: ~15-50ms
- Detection to STT activation: ~50ms
- Total: ~100ms (imperceptible)

### Memory
- Porcupine library: ~20MB
- Loaded model: ~10MB
- Audio buffer: ~1MB
- Total: ~30MB

## Future Enhancements

1. **Multiple Wake Words**: Support different triggers per device/context
2. **Speaker Verification**: Only activate for registered user's voice
3. **Wake Word Learning**: Auto-adapt to user's pronunciation
4. **Wake Word Confidence Tuning**: Adjust per-user sensitivity
5. **Wake Word Analytics**: Track false positives/negatives
