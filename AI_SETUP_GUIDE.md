# AI Voice Assistant Calendar - Setup Guide

## 🤖 What is This?

This is a **complete AI-driven voice assistant calendar** system where:

- **Every command goes through AI** - No pattern matching, no regex
- **AI interprets intent** - The model decides what you want
- **AI generates responses** - Natural language feedback to the user
- **Clean architecture** - Separation of concerns: AI, Calendar, Frontend, Voice

---

## 📋 Project Structure

```
.
├── app_ai.py                          # Main Flask app with AI routing
├── ai_intent_handler.py               # AI Interpreter (intent extraction)
├── ai_response.py                     # AI Response Generator (friendly responses)
├── calendar_service.py                # Google Calendar API wrapper
├── voice_utils.py                     # Voice processing utilities
├── ai_prompts/
│   └── system_prompt.txt              # Instructions for AI model
├── templates/
│   ├── index.html                     # Main dashboard (AI Powered badge)
│   └── login.html                     # Google OAuth login
├── static/
│   ├── script.js                      # Frontend voice + AI integration
│   └── styles.css                     # Modern UI with debug panel
└── requirements-ai.txt                # Python dependencies
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements-ai.txt
```

### 2. Configure Environment

Copy your existing `.env` or create a new one with:

```env
# Flask
FLASK_SECRET=your-secret-key-here
ENV=development
DEBUG=True
FLASK_RUN_PORT=5000

# OpenAI (REQUIRED for AI)
OPENAI_API_KEY=sk-proj-YOUR-KEY-HERE
OPENAI_MODEL=gpt-4o-mini

# Google OAuth (use existing credentials)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/oauth2callback

# Calendar
DEFAULT_TIMEZONE=Africa/Johannesburg
```

### 3. Run the AI App

```bash
python app_ai.py
```

Visit: http://localhost:5000

---

## 🧠 How the AI Works

### Command Flow

```
User says: "Book a meeting tomorrow at 2pm"
     ↓
FRONTEND (Web Speech API)
     ↓
Transcript: "book a meeting tomorrow at 2pm"
     ↓
BACKEND: POST /api/command
     ↓
AI INTERPRETER (ai_intent_handler.py)
     ↓
AI reads system prompt from ai_prompts/system_prompt.txt
OpenAI GPT processes: "book a meeting tomorrow at 2pm"
     ↓
AI Response (JSON):
{
  "intent": "create_event",
  "parameters": {
    "title": "meeting",
    "date": "2025-12-01",
    "time": "14:00"
  },
  "confidence": 0.95
}
     ↓
EXECUTE INTENT (Google Calendar)
     ↓
AI RESPONSE GENERATOR (ai_response.py)
     ↓
Generates: "Your meeting has been added for December 1st at 2 PM"
     ↓
FRONTEND displays response + plays audio
     ↓
Calendar updates with new event
```

### Supported Intents

**1. `create_event`**
- Extract: title, date, time, duration
- Example: "Book a doctor appointment on December 15 at 2pm"

**2. `delete_event`**
- Extract: event_title
- Example: "Cancel my doctor appointment"

**3. `show_events`**
- Extract: date_range (today, tomorrow, this week, etc.)
- Example: "What's on my calendar today?"

**4. `unknown`**
- When the AI can't determine intent
- Example: "What's the weather?"

---

## 🤖 Customizing AI Behavior

Edit `ai_prompts/system_prompt.txt` to change how the AI interprets commands.

### Current System Prompt

The system prompt tells GPT exactly how to behave:

```
You are the AI command interpreter for a voice assistant calendar app.
Your job is to extract intent and parameters from natural voice commands.

You MUST respond with ONLY valid JSON. No other text.

Possible intents: "create_event", "delete_event", "show_events", "unknown"

For "create_event":
- Extract: title (event name), date (YYYY-MM-DD), time (HH:MM)
- Example: "book meeting tomorrow at 2pm" → 
  {"intent": "create_event", "parameters": {"title": "meeting", "date": "2025-12-01", "time": "14:00"}}
```

**To customize:**

1. Open `ai_prompts/system_prompt.txt`
2. Modify instructions for intents
3. Add new intents if needed
4. Restart `app_ai.py`

Example customization:

```
Add new intent "reschedule_event":
- Extract: event_title, new_date, new_time
- Example: "Move my meeting from tomorrow to next Tuesday at 3pm"
```

---

## 🎯 API Endpoints

### POST `/api/command`

Send a voice transcript to the AI.

**Request:**
```json
{
  "transcript": "book meeting tomorrow at 2pm"
}
```

**Response:**
```json
{
  "success": true,
  "intent": "create_event",
  "parameters": {
    "title": "meeting",
    "date": "2025-12-01",
    "time": "14:00"
  },
  "confidence": 0.95,
  "ai_response": "Your meeting has been added for December 1st at 2 PM",
  "execution_result": {
    "success": true,
    "event_id": "...",
    "message": "✅ Created event 'meeting'"
  }
}
```

### GET `/api/events`

Get all calendar events.

**Response:**
```json
{
  "success": true,
  "events": [
    {
      "id": "...",
      "title": "Meeting",
      "date": "2025-12-01",
      "time": "14:00"
    }
  ]
}
```

---

## 🐛 Debug Mode

When `DEBUG=True` in `.env`, the frontend shows a debug panel with:

- Raw AI output
- Extracted intent and parameters
- Confidence scores
- Execution results

This helps verify the AI is making correct decisions.

---

## 🧪 Testing

### Test via Python CLI

```bash
# Test AI interpretation
python ai_intent_handler.py "book meeting tomorrow at 2pm"

# Test AI response generation
python ai_response.py create_event '{"title": "Meeting"}' '{"success": true}'
```

### Test via Frontend

1. Click 🎤 button
2. Say: "Book a meeting tomorrow at 2pm"
3. See AI response and calendar update

---

## 📊 Module Reference

### `ai_intent_handler.py`

**Main function:** `interpret(text: str) -> dict`

```python
import asyncio
import ai_intent_handler

# Async usage
result = asyncio.run(ai_intent_handler.interpret("book meeting tomorrow"))

# Sync usage
result = ai_intent_handler.interpret_sync("book meeting tomorrow")

# Result structure:
{
  "success": bool,
  "intent": str,
  "parameters": dict,
  "confidence": float,
  "raw_response": str
}
```

### `ai_response.py`

**Main function:** `generate_response(intent, parameters, result, success) -> str`

```python
import asyncio
import ai_response

response = asyncio.run(ai_response.generate_response(
  intent="create_event",
  parameters={"title": "Meeting", "date": "2025-12-01", "time": "14:00"},
  result={"success": True, "event_id": "..."},
  success=True
))

# Result: "Your meeting has been added for December 1st at 2 PM"
```

### `calendar_service.py`

```python
from calendar_service import GoogleCalendarService
from google.oauth2.credentials import Credentials

service = GoogleCalendarService(client_secret_file, credentials)

# Get events
events = service.get_events()

# Create event
result = service.create_event(
  title="Meeting",
  date="2025-12-01",
  time="14:00",
  duration=60
)

# Delete event
success = service.delete_event(event_id)

# Find event by title
event = service.find_event_by_title("Meeting")
```

### `voice_utils.py`

```python
import voice_utils

# Validate
is_valid_date("2025-12-01")  # True
is_valid_time("14:00")        # True

# Parse relative dates
date = voice_utils.parse_relative_date("tomorrow")  # "2025-12-01"

# Format for display
formatted = voice_utils.format_date_for_display("2025-12-01")  # "Monday, December 01"
formatted_time = voice_utils.format_time_for_display("14:00")   # "2:00 PM"
```

---

## ❌ Troubleshooting

### "OpenAI API key not configured"

**Fix:** Add `OPENAI_API_KEY` to `.env`

```bash
export OPENAI_API_KEY=sk-proj-YOUR-KEY
```

### "Calendar service unavailable"

**Fix:** Ensure Google OAuth credentials are valid

1. Check `.config/client_secret_*.json` exists
2. Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`
3. Re-authenticate by logging out and back in

### "AI responds with 'unknown'"

**Possible causes:**

1. System prompt is too strict
2. Your command is out of scope
3. AI confidence is low

**Solution:** Edit `ai_prompts/system_prompt.txt` to be more permissive or add new intents

### "Speech recognition not working"

**Fix:** Ensure:

1. HTTPS in production (Chrome requires it for microphone)
2. Browser has microphone permissions
3. Microphone is connected and working

### "Events not showing in calendar"

**Check:**

1. Are you authenticated with Google?
2. Is the calendar ID 'primary' correct?
3. Check browser console for errors

---

## 🚀 Deployment

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Use HTTPS (not HTTP)
- [ ] Use strong `FLASK_SECRET`
- [ ] Store secrets in environment, not `.env`
- [ ] Test all intents
- [ ] Enable CORS only for your domain
- [ ] Monitor OpenAI API usage/costs
- [ ] Set up error logging

### Docker Deployment

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements-ai.txt .
RUN pip install -r requirements-ai.txt
COPY . .
CMD ["python", "app_ai.py"]
```

---

## 📝 Examples

### Example 1: Create Event

**User says:** "Schedule a team meeting next Tuesday at 10 AM for 90 minutes"

**AI Interpretation:**
```json
{
  "intent": "create_event",
  "parameters": {
    "title": "team meeting",
    "date": "2025-12-02",
    "time": "10:00",
    "duration": 90
  }
}
```

**AI Response:** "I've scheduled your team meeting for next Tuesday, December 2nd at 10 AM for 90 minutes"

**Result:** Event created on Google Calendar

---

### Example 2: Delete Event

**User says:** "Cancel my doctor appointment"

**AI Interpretation:**
```json
{
  "intent": "delete_event",
  "parameters": {
    "event_title": "doctor appointment"
  }
}
```

**AI Response:** "I've cancelled your doctor appointment"

**Result:** Event deleted from Google Calendar

---

### Example 3: Show Events

**User says:** "What's on my calendar this week?"

**AI Interpretation:**
```json
{
  "intent": "show_events",
  "parameters": {
    "date_range": "this week"
  }
}
```

**AI Response:** "You have 5 events this week: Monday at 9 AM, Tuesday at 2 PM..."

**Result:** Events displayed in right panel

---

## 🤝 Contributing

To add new intents:

1. Edit `ai_prompts/system_prompt.txt` - Add instructions for new intent
2. Edit `app_ai.py` - Add `elif intent == 'new_intent':` in `_execute_intent()`
3. Test via CLI and frontend

---

## 📞 Support

**Having issues?**

1. Check `.env` configuration
2. Review console logs for errors
3. Enable DEBUG mode to see AI decisions
4. Test AI interpretation directly: `python ai_intent_handler.py "your command"`

---

## 🎉 You're Ready!

Your AI Voice Assistant Calendar is ready to use. Start by:

1. **Running the app:** `python app_ai.py`
2. **Opening browser:** http://localhost:5000
3. **Logging in:** Sign in with Google
4. **Speaking commands:** Click 🎤 and say "book a meeting tomorrow"
5. **Seeing magic:** Watch AI interpret, execute, and respond

**The AI is the center of everything.** No hardcoded logic. Pure AI-driven command interpretation.

---

Enjoy your AI-powered calendar assistant! 🚀🤖📅
