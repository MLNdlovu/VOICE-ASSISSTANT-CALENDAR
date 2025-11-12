# Voice Assistant Calendar - Quick Start

Welcome! Your Voice Assistant Calendar is ready to use in **two ways**:

## Option 1: Desktop GUI (Recommended for Voice)

**Best for:**
- Voice commands & speech recognition
- Local, no internet needed
- Full desktop experience

**Start it:**
```bash
python voice_assistant_calendar.py
```

Then choose:
1. **GUI Dashboard** (graphical interface with all features)
2. **CLI - Voice input** (command line with microphone)
3. **CLI - Text input** (command line, type commands)

**Features:**
- 🎤 Voice input & AI assistant (ChatGPT)
- 📅 Book, cancel, reschedule events
- ⏰ Set reminders & add events
- 🤖 AI-powered suggestions
- 🎨 Beautiful dark theme GUI

---

## Option 2: Web Dashboard (Recommended for Multi-Device)

**Best for:**
- Access from phone, tablet, laptop
- Share calendar with others
- Modern web interface
- No voice needed

**Start it:**
```bash
python web_app.py
```

Then open in browser:
```
http://localhost:5000
```

**Features:**
- 🌐 Works in any browser
- 📱 Mobile-friendly responsive design
- 🔐 Google OAuth login
- 📅 Full calendar management
- ⚙️ Settings & preferences

---

## Running Both Together

You can run **both at the same time** on different ports:

### Terminal 1: Desktop GUI
```bash
python voice_assistant_calendar.py
```
Choose option: `1` (GUI Dashboard)

### Terminal 2: Web Dashboard
```bash
python web_app.py
```
Open: `http://localhost:5000`

They share the **same calendar**, so changes appear everywhere!

---

## First-Time Setup

### 1. Google OAuth Credentials
You need a Google client secret JSON file:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download JSON file and place it in `.config/` folder

Name it: `client_secret_*.json`

### 2. Install Dependencies
```bash
pip install -r requirements-voice.txt
```

### 3. Choose Your Interface
- **Voice + Desktop?** → Run: `python voice_assistant_calendar.py` → Choose GUI
- **Browser + Mobile?** → Run: `python web_app.py` → Open `http://localhost:5000`
- **Both?** → Run both in separate terminals

---

## Common Commands (Voice & Text)

### Booking
- **"Book a slot for Python help tomorrow at 2pm"**
- **"Add meeting with Alex on friday at 10 am"**
- **"Schedule study session on 23 march 2026 at 3pm"**

### Canceling
- **"Cancel my booking on friday at 9am"**
- **"Delete meeting tomorrow at 2pm"**

### Reminders
- **"Set reminder for gym on monday at 6pm"**
- **"Remind me about project deadline on 25th"**

### Viewing
- **"Show my events"**
- **"What's on my calendar?"**

### AI Help
- **"Assistant, suggest a good time for a meeting"**
- **"Ask AI when I'm free tomorrow"**

---

## Settings

### GUI Settings
Click "Settings" in the header:
- Client Secret selection
- Timezone (Africa/Johannesburg, UTC, etc.)
- Default event duration (15-480 min)
- Switch between users

### Web Settings
Click "⚙️ Settings" tab:
- Timezone preference
- Default duration
- Settings auto-save

---

## Troubleshooting

### "Client secret not found"
✓ Place `client_secret_*.json` in `.config/` folder

### "Port 5000 already in use"
✓ Change port: `python web_app.py --port 5001`

### Microphone not working
✓ Install PyAudio: `pip install pyaudio`
✓ Grant microphone permissions in OS

### OAuth fails
✓ Check internet connection
✓ Clear browser cookies & login again

---

## Features Overview

| Feature | GUI | Web |
|---------|-----|-----|
| 🎤 Voice Commands | ✅ | ⏸️ |
| 🤖 ChatGPT AI | ✅ | ⏸️ |
| 📱 Mobile Access | ❌ | ✅ |
| 🌐 Browser Based | ❌ | ✅ |
| 📅 Calendar View | ✅ | ✅ |
| ➕ Add Events | ✅ | ✅ |
| 🗑️ Cancel Events | ✅ | ✅ |
| ⚙️ Settings | ✅ | ✅ |
| 👥 Multi-User | ✅ | ✅ |

---

## Next Steps

1. **For voice:** Run GUI, enable microphone in settings
2. **For web:** Run `python web_app.py`, share URL with friends
3. **For mobile:** Use web dashboard on your phone
4. **For AI:** Set `OPENAI_API_KEY` environment variable for ChatGPT

---

## Support & Documentation

- 📖 **GUI Guide:** See GUI app help menu
- 🌐 **Web Guide:** See `WEB_DASHBOARD.md`
- 🎤 **Voice Guide:** See `VOICE_QUICK_START.md`
- 🤖 **AI Guide:** See `CHATGPT_SETUP.md`

---

## That's it! 🎉

Your Voice Assistant Calendar is ready. Pick your favorite way to use it and start managing your schedule!

**Questions?** Check the docs or explore the app's Help menu.
