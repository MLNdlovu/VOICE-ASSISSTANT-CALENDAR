# Voice Assistant Calendar

## Overview
Voice Assistant Calendar is an AI-powered, voice-enabled scheduling and calendar management system. It integrates with Google Calendar and provides a modern web dashboard, voice command support, and AI (ChatGPT) assistance for booking, managing, and viewing events. The project is designed for students, educators, and professionals who need accessible, hands-free calendar management.

## Features

### Core System (10 Complete Features)
1. **NLU Parser** - Intent extraction & entity recognition from natural language
2. **Smart Scheduler** - Intelligent meeting booking with conflict resolution
3. **Agenda Summaries** - Automatic meeting recap and action item generation
4. **Pattern Detection** - Emotional awareness & schedule pattern analysis
5. **Email Drafting** - Automated professional email generation
6. **Voice Sentiment** - Emotion detection from voice input
7. **Task Extraction** - Automatic action item extraction from meetings
8. **Jarvis Conversations** - Multi-turn conversation management
9. **Visual Calendar** - Heatmaps, stress analysis, availability graphs ⭐ **[NEW]**
10. **AI Accessibility** - Audio-only UI, voice correction, adaptive speech ⭐ **[NEW]**

### Interface & Integration
- **Web Dashboard**: Modern Flask-based web app for managing events, bookings, and settings.
- **Google Calendar Integration**: OAuth2 authentication and full event management (view, book, cancel, update).
- **Voice Commands**: Book, cancel, and view events using natural language voice input.
- **AI Assistant**: ChatGPT integration for smart scheduling, agenda generation, and calendar Q&A.
- **Accessibility**: Voice input/output and accessible UI for users with different needs.
- **Visual Analytics**: Calendar heatmaps showing intensity, stress levels, and availability.
- **Audio-Only Mode**: Complete accessibility for blind and low-vision users.
- **GUI (Legacy)**: Tkinter-based GUI (now deprecated in favor of the web dashboard).
- **CLI Support**: Command-line interface for advanced users.
- **Testing**: Pytest-based test suite with 270+ tests.

## Target Market
- Students and educators needing efficient, hands-free scheduling.
- Professionals and organizations seeking accessible, AI-powered calendar tools.
- **People with disabilities, blind and visually impaired users who need voice-first, accessible scheduling.**
- Users with accessibility needs who prefer or require voice interfaces.
- Tech-savvy individuals interested in AI and productivity automation.

## Target audience
This project is designed for people with disabilities, with a focus on blind and visually impaired users who benefit from voice-first calendar interaction and accessible UX.

## Accessibility goals
- Voice-driven calendar management (create, read, update, delete events by speech)
- Audio feedback and confirmations for all actions
- Screen-reader friendly text output and semantic structure
- High-contrast and scalable UI options (for low-vision users)
- Keyboard-only navigation and clear focus indicators

## Quick Start
1. **Clone the repository**
2. **Install dependencies**:
   ```sh
   pip install -r requirements-voice.txt
   ```
3. **Configure Google OAuth**:
   - Place your Google `client_secret_*.json` in the `.config/` directory.
4. **Run the web app**:
   ```sh
   python web_app.py
   ```
   Open [http://localhost:5000](http://localhost:5000) in your browser.

## Voice Commands Examples
- "Book a slot on 2025-11-20 at 10:30"
- "Cancel my booking on 2025-11-20 at 10:30"
- "Show me upcoming events"
- "Help"

## AI Assistant Examples
- "Suggest the best time for a meeting next week"
- "Summarize my meetings for today"
- "Draft a follow-up email for my last event"
- "What's my busiest day this week?" (Visual Calendar)
- "Enable audio-only mode" (Accessibility)
- "Book at 11... wait no, 11:30" (Voice Correction)

## Project Structure
- `web_app.py` — Main Flask web server
- `src/` — Core modules (13 total):
  - AI features (NLU, patterns, sentiment, scheduler AI)
  - Visual analytics (visual_calendar.py - Feature 9)
  - Accessibility (accessibility.py - Feature 10)
  - Conversation management (Jarvis)
  - Email drafting, task extraction, agenda summarization
- `voice_handler.py` — Voice command parsing and TTS
- `tests/` — Automated test suite (270+ tests)
- `docs/` — Comprehensive documentation:
  - `VISUAL_CALENDAR_GUIDE.md` — Feature 9 complete guide
  - `ACCESSIBILITY_GUIDE.md` — Feature 10 complete guide
  - Plus 6 other documentation files
- `templates/` and `static/` — Web UI assets
- `requirements-voice.txt` — Python dependencies

## Dependencies
- Flask, Google API Python Client, google-auth-oauthlib
- SpeechRecognition, PyAudio, pyttsx3 (voice)
- openai, python-dotenv (AI)
- prettytable, tkcalendar
- pytest (testing)

## Example Calendar Event (JSON)
```
{
  "summary": "Meeting",
  "start": {"dateTime": "2025-11-20T10:30:00+02:00"},
  "end": {"dateTime": "2025-11-20T11:00:00+02:00"},
  "attendees": [
    {"email": "user@example.com"}
  ]
}
```

## Contributing
Pull requests and suggestions are welcome! Please see the `docs/` folder for more information.

### Documentation Files
- **Feature Guides**: See `docs/VISUAL_CALENDAR_GUIDE.md` and `docs/ACCESSIBILITY_GUIDE.md` for detailed feature documentation
- **Implementation Details**: See `FEATURES_9_10_IMPLEMENTATION_SUMMARY.md`, `FEATURES_9_10_COMPLETION_REPORT.md`, and `FEATURES_9_10_QUICK_REFERENCE.md`
- **Quick Navigation**: See `FEATURES_9_10_INDEX.md` for complete documentation index

### System Statistics
- **Production Code**: 5,500+ lines across 13 modules
- **Test Suite**: 270+ passing tests
- **Documentation**: 3,500+ lines
- **API Endpoints**: 20+
- **Features**: 10 complete, production-ready features

## License
MIT License

---
For more details, see the documentation in the `docs/` folder and the code comments in each module.

## How to highlight this on GitHub
- Add the above text to your README so it appears on the project homepage.
- Add repository topics: accessibility, blind, visually-impaired, disability, voice-assistant, calendar.
- Set the repo description to mention accessibility and blind/visually-impaired target audience.
For more details, see the documentation in the `docs/` folder and the code comments in each module.
