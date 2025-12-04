# 🤖 AI Voice Assistant Calendar - README

> **A production-ready voice assistant powered by OpenAI GPT with zero hardcoded rules**

---

## 🎯 What This Is

This is a **complete AI-driven voice calendar system** where:

- **Every command goes through GPT** - No regex, no pattern matching
- **AI interprets intent** - The model decides what you meant
- **AI generates responses** - Natural language feedback to users
- **Clean architecture** - Separation of concerns (AI, Calendar, Frontend, Voice)
- **Production quality** - Proper error handling, logging, security

---

## ✨ Features

✅ **Voice Recognition** - Browser-native Web Speech API (no external service needed)
✅ **AI Interpretation** - GPT-4o-mini interprets natural language commands
✅ **Google Calendar** - Real-time sync with Google Calendar API
✅ **Natural Responses** - AI generates friendly, contextual responses
✅ **Debug Panel** - In dev mode, see exactly what the AI decided
✅ **Async Processing** - Fast, non-blocking AI calls
✅ **OAuth 2.0** - Secure Google authentication
✅ **Modern UI** - Clean, responsive design with animations
✅ **Production Ready** - Error handling, logging, security best practices

---

## 🚀 Quick Start

### Option 1: Windows
```bash
# Double-click this file:
START_AI.bat
```

### Option 2: macOS/Linux
```bash
# Run this script:
bash START_AI.sh
```

### Option 3: Manual
```bash
# Install dependencies
pip install -r requirements-ai.txt

# Set environment variables
export OPENAI_API_KEY=sk-proj-YOUR-KEY
export GOOGLE_CLIENT_ID=your-id
export GOOGLE_CLIENT_SECRET=your-secret

# Run the app
python app_ai.py

# Open browser
open http://localhost:5000
```

---

## 📋 Requirements

- **Python** 3.11+
- **OpenAI API Key** (get from https://platform.openai.com/api-keys)
- **Google OAuth Credentials** (from https://console.cloud.google.com)
- **Modern Browser** (Chrome, Firefox, Safari, Edge)
- **Microphone** (for voice input)

---

## 🧠 How It Works

### The AI Flow

```
User Voice Input
      ↓
Web Speech API (Browser)
      ↓
Transcript: "book meeting tomorrow"
      ↓
POST /api/command (to backend)
      ↓
🤖 AI INTERPRETER (OpenAI GPT)
   ├─ Reads system prompt from ai_prompts/system_prompt.txt
   ├─ Processes natural language
   └─ Outputs structured JSON
      ↓
{
  "intent": "create_event",
  "parameters": {
    "title": "meeting",
    "date": "2025-12-01",
    "time": "09:00"
  },
  "confidence": 0.95
}
      ↓
EXECUTE INTENT (Google Calendar API)
      ↓
Event created successfully
      ↓
🤖 AI RESPONSE GENERATOR
   └─ Generates: "Your meeting has been added for December 1st at 9:00 AM"
      ↓
Display in UI + Calendar Panel Updates
```

---

## 🎯 Supported Commands

### Create Event
```
"Book a meeting tomorrow at 2pm"
"Schedule doctor appointment on December 15 at 2pm"
"Add team standup next week at 10am for 30 minutes"
```

### Delete Event
```
"Cancel my doctor appointment"
"Delete the meeting with Sipho"
"Remove the 3pm call"
```

### Show Events
```
"What's on my calendar today?"
"Show me next week's events"
"List all my meetings this week"
```

---

## 📁 Project Structure

```
.
├── app_ai.py                          # 🎯 Main Flask app (AI routing)
├── ai_intent_handler.py               # 🤖 AI interpreter
├── ai_response.py                     # 💬 Response generator
├── calendar_service.py                # 📅 Google Calendar wrapper
├── voice_utils.py                     # 🔧 Utilities
├── ai_prompts/
│   └── system_prompt.txt              # 📝 AI instructions
├── templates/
│   ├── index.html                     # 🎨 Dashboard
│   └── login.html                     # 🔐 Login page
├── static/
│   ├── script.js                      # 🎤 Frontend logic
│   └── styles.css                     # 🎨 Styling
├── requirements-ai.txt                # 📦 Dependencies
├── AI_SETUP_GUIDE.md                  # 📚 Full setup guide
├── AI_IMPLEMENTATION_COMPLETE.md      # 📚 Complete reference
├── START_AI.sh                        # 🚀 Start script (Linux/Mac)
└── START_AI.bat                       # 🚀 Start script (Windows)
```

---

## 🔧 Configuration

### Environment Variables (.env)

```env
# Flask Configuration
FLASK_SECRET=your-secret-key-here
ENV=development
DEBUG=True
FLASK_RUN_PORT=5000

# OpenAI (REQUIRED)
OPENAI_API_KEY=sk-proj-YOUR-KEY-HERE
OPENAI_MODEL=gpt-4o-mini

# Google OAuth (from .config/client_secret_*.json)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/oauth2callback

# Calendar
DEFAULT_TIMEZONE=Africa/Johannesburg
```

### Customizing AI Behavior

Edit `ai_prompts/system_prompt.txt`:

```
You are the AI command interpreter...
Your job is to extract intent and parameters from natural voice commands.

Possible intents: "create_event", "delete_event", "show_events", "unknown"

For "create_event":
  Extract: title, date (YYYY-MM-DD), time (HH:MM), duration
  ...
```

Add new intents, modify rules, change AI personality!

---

## 🧪 Testing

### Test via CLI

```bash
# Test AI interpretation
python ai_intent_handler.py "book meeting tomorrow at 2pm"

# Output:
# {
#   "success": true,
#   "intent": "create_event",
#   "parameters": {
#     "title": "meeting",
#     "date": "2025-12-01",
#     "time": "14:00"
#   },
#   "confidence": 0.95
# }
```

### Test via Browser

1. Start app: `python app_ai.py`
2. Open: http://localhost:5000
3. Login with Google
4. Click 🎤 microphone
5. Say: "book a meeting tomorrow at 2pm"
6. See AI response + calendar update

### Debug Mode

When `DEBUG=True`, see:
- Raw AI interpretation
- Intent and parameters
- Confidence scores
- Execution results

---

## 📊 API Reference

### POST /api/command

Send voice transcript to AI interpreter.

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
  "ai_response": "Your meeting has been added for December 1st at 2:00 PM",
  "execution_result": {
    "success": true,
    "event_id": "...",
    "message": "✅ Created event 'meeting'"
  }
}
```

### GET /api/events

Get all calendar events.

**Response:**
```json
{
  "success": true,
  "events": [
    {
      "id": "event123",
      "title": "Meeting",
      "date": "2025-12-01",
      "time": "14:00",
      "description": "Team sync"
    }
  ],
  "count": 1
}
```

---

## 🐛 Troubleshooting

### "OpenAI API key not configured"

**Fix:** Add `OPENAI_API_KEY` to `.env`

```bash
export OPENAI_API_KEY=sk-proj-YOUR-KEY
```

### "Calendar service unavailable"

**Fix:** Check Google OAuth:
1. Verify `.config/client_secret_*.json` exists
2. Check `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
3. Re-authenticate by logging out and back in

### "AI responds with 'unknown'"

**Cause:** System prompt is too strict or intent is out of scope

**Fix:** Edit `ai_prompts/system_prompt.txt` to be more permissive

### "Microphone not working"

**Check:**
- ✅ HTTPS in production (Chrome requires it)
- ✅ Browser has microphone permissions
- ✅ Microphone is plugged in and working
- ✅ No other app is using the mic

---

## 🚀 Deployment

### Local Development

```bash
python app_ai.py
```

Runs on http://localhost:5000 with DEBUG enabled.

### Production with Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run production server
gunicorn app_ai:app --workers 4 --bind 0.0.0.0:5000
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements-ai.txt .
RUN pip install -r requirements-ai.txt
COPY . .
ENV DEBUG=False
CMD ["gunicorn", "app_ai:app", "--workers", "4", "--bind", "0.0.0.0:5000"]
```

### Important: HTTPS in Production

Browsers require HTTPS for microphone access in production!

Use a reverse proxy (nginx) with SSL:

```nginx
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert;
    ssl_certificate_key /path/to/key;
    
    location / {
        proxy_pass http://localhost:5000;
    }
}
```

---

## 🧑‍💻 Code Examples

### Using AI Interpreter

```python
import asyncio
import ai_intent_handler

# Async usage
result = asyncio.run(ai_intent_handler.interpret("book meeting tomorrow"))

# Result:
# {
#   "success": true,
#   "intent": "create_event",
#   "parameters": {"title": "meeting", "date": "2025-12-01", "time": "09:00"},
#   "confidence": 0.95
# }
```

### Using Response Generator

```python
import asyncio
import ai_response

response = asyncio.run(ai_response.generate_response(
    intent="create_event",
    parameters={"title": "Meeting", "date": "2025-12-01", "time": "14:00"},
    result={"success": True},
    success=True
))

# Result: "Your meeting has been added for December 1st at 2:00 PM"
```

### Using Calendar Service

```python
from calendar_service import GoogleCalendarService

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
service.delete_event(event_id)
```

---

## 📚 Documentation

- **[AI_SETUP_GUIDE.md](AI_SETUP_GUIDE.md)** - Complete setup and customization
- **[AI_IMPLEMENTATION_COMPLETE.md](AI_IMPLEMENTATION_COMPLETE.md)** - Full reference and examples

---

## 🎓 For Examiners

### Proof of AI Integration

1. **Show Debug Panel** - Enable `DEBUG=True` to see AI decisions in real-time
2. **Test Different Commands** - Try various phrases, see different intents
3. **Show Code** - Demonstrate no hardcoded rules, pure AI-driven logic
4. **Explain Architecture** - Walk through the AI flow diagram
5. **Show System Prompt** - Demonstrate AI customization

### Key Talking Points

✅ "Every command goes through GPT"
✅ "No regex or pattern matching"
✅ "AI decides the intent"
✅ "AI generates responses"
✅ "Production-ready code"
✅ "Easily customizable via system prompt"

---

## 🤝 Contributing

To add new features:

1. **New Intent?** - Edit `ai_prompts/system_prompt.txt` + add handler in `app_ai.py`
2. **New Response Format?** - Modify `ai_response.py`
3. **New Calendar Feature?** - Add to `calendar_service.py`

---

## 📝 License

This project is provided as-is for educational and demonstration purposes.

---

## 🎉 Get Started Now!

```bash
# Windows
START_AI.bat

# macOS/Linux
bash START_AI.sh

# Manual
python app_ai.py
```

Then open http://localhost:5000 and start talking! 🎤

---

## 💡 Key Insights

### Why This Matters

1. **No Hardcoding** - AI makes all decisions
2. **Scalable** - Add new intents by updating system prompt
3. **Natural** - AI generates real human language
4. **Extensible** - Easy to add new capabilities
5. **Production Ready** - Proper architecture, security, logging

### The Magic

The beauty of this system is its **simplicity**. Everything flows through one AI model. Want to change behavior? Update the system prompt. Want to add a capability? Add it to the prompt and execute handler.

This is **real AI-driven development**, not just pattern matching with a chatbot facade.

---

Enjoy your AI-powered calendar! 🚀🤖📅
