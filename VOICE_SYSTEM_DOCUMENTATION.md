# Voice Assistant System Implementation Guide

## Overview

A comprehensive voice-enabled calendar assistant with AI integration, natural language processing, conflict detection, and premium animations.

## Features Implemented

### 1. **Voice Engine** (`src/voice_engine.py`)
- **Speech Recognition**: Google Speech-to-Text integration via `speech_recognition` library
- **Text-to-Speech**: Natural voice synthesis via `pyttsx3`
- **Trigger Detection**: User-defined wake words (2 letters + 2 numbers format, e.g., "EL25")
- **Conversation Management**: Context tracking and multi-turn dialogue support
- **State Management**: Real-time listening/speaking state tracking

**Key Classes:**
- `VoiceState`: Dataclass tracking current voice state
- `VoiceEngine`: Main voice processing engine with:
  - `speak()`: Generate audio output
  - `listen()`: Capture voice input
  - `detect_trigger()`: Recognize user wake word
  - `wait_for_trigger()`: Listen for trigger phrase
  - `start_active_listening()`: Continuous background listening
  - `stop_active_listening()`: Deactivate voice mode

### 2. **Command Processor** (`src/command_processor.py`)
- **Intent Detection**: Automatic identification of user intent
- **Parameter Extraction**: Natural language parsing for meeting details
- **Command Types**:
  - `BOOK_MEETING`: Schedule new events
  - `LIST_EVENTS`: Retrieve calendar events
  - `SET_REMINDER`: Create reminders
  - `ASK_QUESTION`: General questions (delegated to AI)
  - `SMALL_TALK`: Casual conversation

**Pattern Matching:**
```python
# Examples of recognized patterns:
"Book a meeting with John tomorrow at 2pm"
"What events do I have today?"
"Set a reminder for 3pm"
"Hello, how are you?"
```

**Extracted Parameters:**
- `title`: Meeting name/topic
- `date`: Scheduled date
- `time`: Start time (HH:MM format)
- `duration`: Meeting length in minutes
- `attendees`: List of participants

### 3. **Calendar Conflict Detector** (`src/calendar_conflict.py`)
- **Conflict Detection**: Identifies overlapping meetings
- **Alternative Suggestions**: Proposes free time slots
- **Availability Summary**: Shows busy/free times for a given date
- **Conflict Resolution**: Offers options to move, cancel, or overwrite

**Key Methods:**
```python
detector = ConflictDetector(timezone='Africa/Johannesburg')

# Detect conflicts
conflicts = detector.detect_conflicts(proposed_slot, existing_events)

# Get alternatives
suggestions = detector.suggest_alternatives(
    proposed_slot, 
    existing_events, 
    duration_minutes=30,
    search_days=7
)

# Get availability for a date
availability = detector.get_availability_summary(
    existing_events, 
    date_str='2024-01-15'
)
```

### 4. **Conversation Logger** (`src/conversation_logger.py`)
- **SQLite Database**: Persistent conversation storage
- **Session Tracking**: Group interactions into sessions
- **Intent Statistics**: Analyze command usage patterns
- **Error Tracking**: Monitor common failures
- **Analytics**: Response times, success rates, user behavior

**Database Schema:**
- `conversations`: Individual turns with user input, AI response, intent, parameters
- `sessions`: User sessions with timestamps
- `intent_stats`: Aggregated statistics by intent and date

**Usage:**
```python
logger = ConversationLogger()

# Start session
logger.start_session(session_id, user_id)

# Log turn
log = ConversationLog(
    session_id=session_id,
    user_id=user_id,
    turn_number=1,
    user_input="Book a meeting",
    assistant_response="I can help you book a meeting",
    intent="book_meeting",
    extracted_parameters={'title': 'Team meeting'}
)
logger.log_turn(log)

# Get stats
stats = logger.get_user_statistics(user_id, days=7)
```

### 5. **Voice Assistant UI** (`static/voice-assistant.js`)
- **Web Speech API Integration**: Browser-based speech recognition
- **Real-time Transcription**: Display recognized text
- **TTS Feedback**: Speak responses back to user
- **Chat Interface**: Message history with speaker labels
- **State Management**: Track listening/speaking states

**Key Methods:**
```javascript
voiceAssistant.initializeVoiceAssistant()  // Start session
voiceAssistant.startListening()            // Begin voice capture
voiceAssistant.processVoiceCommand(text)   // Send to backend
voiceAssistant.speak(text)                 // Speak response
voiceAssistant.displayMessage(speaker, text)  // Show transcript
voiceAssistant.endSession()                // End session
```

### 6. **Premium Animations** (`static/voice-animations.css`)
- **Glowing Pulse Rings**: 3-layer expanding circles when listening
- **Waveform Visualization**: 8-bar animated waveform
- **Status Indicator**: Blinking dot showing state (listening/speaking/idle)
- **Smooth Transitions**: Fade-in/slide-in animations for messages
- **Responsive Design**: Mobile-optimized animations

**Animations:**
- `pulse-listening-1/2/3`: Expanding rings with increasing opacity
- `waveform-listening`: Rising bars responding to voice input
- `pulse-speaking`: Breathing pulse effect while speaking
- `transcript-appear`: Smooth message appearance

### 7. **Web API Endpoints** (in `web_app.py`)

#### POST `/api/voice/start`
Initialize voice session
```json
{
  "success": true,
  "session_id": "user@email.com_1234567890",
  "user_trigger": "EL25",
  "user_name": "Ellen"
}
```

#### POST `/api/voice/process-command`
Process voice command
```json
{
  "text": "Book a meeting with John tomorrow at 2pm"
}
```
Response:
```json
{
  "success": true,
  "command_type": "book_meeting",
  "confidence": 0.95,
  "parameters": {
    "title": "Meeting with John",
    "date": "tomorrow",
    "time": "14:00",
    "attendees": ["John"]
  },
  "message": "I can help you book that meeting"
}
```

#### POST `/api/voice/end-session`
End voice session and save logs
```json
{
  "success": true,
  "message": "Session ended"
}
```

#### GET `/api/voice/stats?days=7`
Get usage statistics
```json
{
  "success": true,
  "statistics": {
    "user_id": "user@email.com",
    "period_days": 7,
    "total_turns": 42,
    "success_rate": 94.5,
    "average_response_time_ms": 450.2,
    "intent_breakdown": [
      {"intent": "book_meeting", "count": 15},
      {"intent": "list_events", "count": 20}
    ]
  }
}
```

## User Voice Triggers

Format: 2 uppercase letters + 2 digits (e.g., "EL25")

**Setup Process:**
1. User registers with name, surname, email
2. Enters custom voice trigger during registration
3. Trigger validated with regex: `^[A-Z]{2}[0-9]{2}$`
4. Stored in session and database
5. Used for wake-word detection

**Voice Interaction Flow:**
```
1. Login complete → Voice greeting: "Hello Ellen!"
2. System announces trigger: "Say your trigger: EL25"
3. User speaks trigger word
4. System detects trigger → "Yes, what can I do for you?"
5. User speaks command: "Book a meeting..."
6. System processes and responds
```

## Conversation Flow Examples

### Example 1: Book Meeting
```
User: "Book a meeting with John tomorrow at 2pm"
Assistant: "I can help you book a meeting"
→ Parameters: title=Meeting with John, date=tomorrow, time=14:00, attendees=[John]
→ Check calendar conflicts
→ Create event or suggest alternatives
```

### Example 2: List Events
```
User: "What events do I have today?"
Assistant: "You have 3 events today: Team standup at 9am, Client call at 11am, Lunch break at 1pm"
→ Retrieve events from calendar
→ Filter by date
→ Speak summary
```

### Example 3: Set Reminder
```
User: "Remind me to call mom at 5pm"
Assistant: "I'll remind you to call mom at 5pm today"
→ Extract: title=call mom, time=17:00
→ Create reminder event with notification
```

### Example 4: Conflict Handling
```
User: "Book a meeting at 2pm tomorrow"
→ Conflict detected: "Client call at 2pm"
Assistant: "That time conflicts with your Client call. Would you like me to suggest alternatives?"
→ Suggest: 2:30pm (free), 3pm (free), 4:30pm (free)
```

## Installation & Requirements

```bash
# Voice recognition and TTS
pip install speech_recognition==3.10.1
pip install pyttsx3==2.90

# For better audio input on Windows
pip install pyaudio==0.2.13

# Already included in requirements-voice.txt
pip install -r requirements-voice.txt
```

## Browser Compatibility

**Web Speech API Support:**
- ✅ Chrome/Chromium (best support)
- ✅ Edge
- ✅ Opera
- ⚠️ Firefox (limited, Mozilla-specific API)
- ❌ Safari (no Web Speech API support)

**Fallback:** If browser doesn't support Web Speech API, users can still type commands manually.

## Database Storage

**Conversation Log Table:**
```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    user_id TEXT,
    turn_number INTEGER,
    user_input TEXT,
    assistant_response TEXT,
    intent TEXT,
    command_type TEXT,
    extracted_parameters JSON,
    success BOOLEAN,
    error_message TEXT,
    response_time_ms REAL,
    audio_duration_ms REAL,
    timestamp DATETIME
);
```

**Access Logs:**
```python
logger = ConversationLogger()
history = logger.get_session_history(session_id)
stats = logger.get_user_statistics(user_id, days=7)
errors = logger.get_common_errors(user_id)
transcript = logger.export_session_transcript(session_id, format='text')
```

## Error Handling

**Common Errors:**
- `"I didn't catch that. Please repeat."` - Speech recognition failed
- `"Your speech input is too quiet. Please speak louder."` - Audio level too low
- `"That time conflicts with..."` - Calendar conflict detected
- `"I need more information about..."` - Missing required parameters
- `"Speech recognition service unavailable"` - API error

**Graceful Degradation:**
- If voice fails, user can type commands manually
- If speech synthesis unavailable, respond with text only
- If database down, still process commands but don't log

## Performance Optimization

- **Trigger Detection**: ~100ms per recognition cycle
- **Command Processing**: ~50-150ms parsing + API call
- **Calendar Query**: ~200-500ms depending on event count
- **Speech Synthesis**: ~500-2000ms depending on text length

**Caching:**
- User trigger cached in session memory
- Calendar events cached with 5-minute TTL
- Command patterns cached for faster intent detection

## Security Considerations

1. **Voice Trigger Storage**: Stored as uppercase letters only, no special chars
2. **Session Isolation**: Each user gets separate voice session
3. **Conversation Logs**: User data encrypted in database (recommended)
4. **Audio**: No raw audio stored, only transcribed text
5. **HTTPS**: Required for production (Web Speech API requirement)

## Customization Options

### Change Voice Gender/Accent:
```javascript
const utterance = new SpeechSynthesisUtterance(text);
utterance.voice = speechSynthesis.getVoices()[0];  // Select voice
utterance.pitch = 1.5;  // 0.5 to 2.0
utterance.rate = 0.8;   // 0.1 to 10.0
```

### Add Custom Intents:
```python
class CommandType(Enum):
    CUSTOM_ACTION = "custom_action"

# Add pattern matching in CommandProcessor
def _matches_custom_pattern(self, text: str) -> bool:
    return "your pattern" in text.lower()
```

### Configure Recognition Language:
```javascript
recognition.lang = 'fr-FR';  // French
recognition.lang = 'es-ES';  // Spanish
recognition.lang = 'de-DE';  // German
```

## Testing

### Unit Tests:
```python
# Test trigger detection
engine = VoiceEngine(user_trigger="EL25")
assert engine.detect_trigger("el25")  # ✓
assert engine.detect_trigger("Ellen Twenty Five")  # ✓
assert engine.detect_trigger("EL 25")  # ✓

# Test command parsing
processor = CommandProcessor()
cmd = processor.parse_command("Book meeting with John at 2pm")
assert cmd.type == CommandType.BOOK_MEETING
assert cmd.parameters['time'] == "14:00"

# Test conflict detection
detector = ConflictDetector()
conflicts = detector.detect_conflicts(slot, existing_events)
assert len(conflicts) > 0
```

## Future Enhancements

1. **Advanced NLP**: Implement RASA or spaCy for better intent detection
2. **Multi-language Support**: Support for Spanish, French, German, etc.
3. **Sentiment Analysis**: Understand user emotion in commands
4. **Voice Biometrics**: Speaker verification for security
5. **Integration with Slack**: Send meeting summaries to team
6. **Calendar Analytics**: Monthly/yearly statistics dashboard
7. **Meeting Transcription**: Record and transcribe meetings
8. **Smart Scheduling**: AI-powered optimal time suggestions
9. **Natural Dialogue**: More conversational, context-aware responses
10. **Custom Workflows**: Create custom voice command sequences

## Troubleshooting

**"Speech recognition not supported":**
- Use Chrome/Edge browser
- Check microphone permissions
- Ensure browser has microphone access

**"Can't find microphone":**
- Check Windows sound settings
- Test microphone with other apps
- Ensure volume is not muted

**"Command not recognized":**
- Speak clearly and at normal pace
- Avoid background noise
- Try rephrasing command

**"Meeting not booked despite successful command":**
- Check calendar conflicts
- Verify date/time format
- Check user has calendar write permissions

**"Database errors":**
- Check `.config/voice_conversations.db` exists
- Verify folder permissions
- Clear old logs: `logger.cleanup_old_data(days_to_keep=90)`

## Support & Debugging

**Enable Verbose Logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# In voice_engine.py
print(f"DEBUG: Detected text: {text}")
print(f"DEBUG: Trigger match confidence: {confidence}")
```

**Browser Console Debugging:**
```javascript
// Check speech API availability
console.log(window.SpeechRecognition ? "Available" : "Not available");

// Monitor recognition events
recognition.onstart = () => console.log('Recognition started');
recognition.onresult = (e) => console.log('Result:', e.results[0][0].transcript);
recognition.onerror = (e) => console.error('Error:', e.error);
```

---

**Version**: 1.0.0  
**Last Updated**: November 2024  
**Author**: Voice Assistant Calendar Team
