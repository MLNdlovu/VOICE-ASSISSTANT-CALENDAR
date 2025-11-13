# 🚀 Voice Assistant Calendar - Complete Project Setup

## Project Overview

**Voice Assistant Calendar** is a hands-free calendar management system that allows you to:
- 🎤 Book code clinic slots using voice commands
- 📅 Manage your Google Calendar
- 🗣️ Hear voice confirmations (text-to-speech)
- 🖥️ Use a GUI dashboard interface
- 🧪 Run comprehensive tests

**Status:** ✅ Production Ready | **Python:** 3.11.9 | **Tests:** 38/38 passing

---

## 📁 Project Structure

After organization, your project should look like this:

```
dbn_12_code_clinics-master/
│
├── 📄 Main Application Files
│   ├── voice_assistant_calendar.py    ⭐ Main application (GUI + Voice + Text modes)
│   ├── voice_handler.py               🎤 Voice recognition & text-to-speech
│   ├── book.py                        📅 Booking logic
│   ├── view.py                        👁️ Calendar display logic
│   ├── get_details.py                 📝 Input utilities
│   ├── gui_dashboard.py               🖥️ Tkinter GUI interface
│   └── gui_enhanced.py                🖥️ Enhanced GUI (alternative)
│
├── 📂 src/                            [Optional] Source code mirror
├── 📂 web/                            🌐 Web dashboard files
│   ├── web_app.py                     Flask web application
│   ├── templates/                     HTML templates
│   └── static/                        CSS & JS files
│
├── 📂 tests/                          🧪 Test suite
│   ├── test_voice_commands.py         38 comprehensive tests
│   ├── test_configuration_code_clinics.py
│   ├── test_get_details.py
│   ├── test_cancel_booking.py
│   └── __init__.py
│
├── 📂 docs/                           📚 Documentation
│   └── All documentation files
│
├── 📂 config/                         ⚙️ Configuration
│   └── .config/                       Google OAuth credentials
│
├── 📄 Configuration Files
│   ├── requirements-voice.txt         📦 Python dependencies
│   ├── .env.example                   Environment template
│   ├── package.json                   Node.js (optional)
│   └── .gitignore                     Git ignore rules
│
├── 📚 Documentation Files
│   ├── README.md                      Project overview
│   ├── PYTHON_311_SETUP.md            Python 3.11.9 setup guide
│   ├── VOICE_QUICK_START.md           5-minute quick start
│   ├── VOICE_INTEGRATION_GUIDE.md     Complete voice guide
│   ├── ENHANCED_FEATURES.md           Feature documentation
│   ├── DEVELOPER_GUIDE.md             For developers
│   ├── DOCUMENTATION_INDEX.md         Documentation index
│   ├── SETUP_INSTRUCTIONS.md          Setup guide
│   ├── VERIFICATION_CHECKLIST.md      Pre-launch checklist
│   ├── COMMANDS_QUICK_REFERENCE.txt   Voice commands list
│   └── WEB_DASHBOARD.md               Web interface guide
│
├── 📂 Demo & Examples
│   ├── enhanced_features_demo.py      Interactive demo
│   ├── voice_examples.py              Voice command examples
│   └── test_gui_setup.py              GUI testing
│
├── 🔧 Utilities
│   ├── ai_chatgpt.py                  ChatGPT integration
│   ├── venv/                          Virtual environment
│   └── .venv/                         Alternative venv
│
└── 📂 System Files
    ├── .git/                          Git repository
    ├── __pycache__/                   Python cache
    ├── .vscode/                       VS Code settings
    ├── node_modules/                  Node.js modules
    └── .pytest_cache/                 Pytest cache
```

---

## ⚡ Quick Start (5 Minutes)

### Step 1: Activate Virtual Environment

```powershell
cd "C:\Users\User\Documents\dbn_12_code_clinics-master"
.\venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies (if not already installed)

```powershell
pip install -r requirements-voice.txt
```

### Step 3: Choose Your Mode and Run

#### GUI Mode (Recommended - Full Featured)
```powershell
python voice_assistant_calendar.py
# When prompted, select: gui
```

#### Voice Mode (Hands-Free)
```powershell
python voice_assistant_calendar.py
# When prompted, select: voice
```

#### Text Mode (No Microphone Needed)
```powershell
python voice_assistant_calendar.py
# When prompted, select: text
```

---

## 🎤 Voice Commands Examples

Once running, try these commands:

### Book Events
```
"Book tomorrow at 2 PM for Python help"
"Schedule in 3 days at 10:00 for database design"
"Book next Monday at 14:00 for interview prep"
```

### View Calendar
```
"Show me upcoming events"
"View my calendar"
"List all events"
```

### Cancel Events
```
"Cancel my booking on 2024-03-15 at 10:00"
"Unbook tomorrow at 2 PM"
```

### Other
```
"Help"
"Settings"
"Exit"
```

---

## 🧪 Running Tests

Run the comprehensive test suite (38 tests):

```powershell
# All tests with verbose output
pytest tests/test_voice_commands.py -v

# Specific test class
pytest tests/test_voice_commands.py::TestRelativeDateParsing -v

# With coverage report
pytest tests/test_voice_commands.py --cov=voice_handler --cov-report=html
```

---

## 📺 Running the Demo

See all features in action:

```powershell
python enhanced_features_demo.py
```

---

## 🌐 Web Dashboard (Optional)

Run the Flask web interface:

```powershell
python web_app.py
```

Then open: `http://localhost:5000`

---

## 📚 Key Features

### ✅ Voice Command Integration
- Speech recognition via Google API
- Natural language processing
- Relative date support (tomorrow, next Monday, in 3 days)
- Automatic voice feedback (text-to-speech)

### ✅ Calendar Management
- Book code clinic slots
- Cancel bookings
- View upcoming events
- Share calendar

### ✅ GUI Dashboard
- View next 7 events in table format
- Add/cancel events with buttons
- Voice integration in GUI
- Settings adjustment panel

### ✅ Testing Suite
- 38 comprehensive tests
- Test voice commands
- Test NLP parsing
- Test date/time extraction
- 100% passing rate

---

## 🔧 Configuration

### Google Calendar Setup

1. Go to: https://console.cloud.google.com
2. Create a new project
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials JSON
6. Place in `.config/client_secret_*.json`

Or use existing credentials if already configured.

### API Keys & Credentials

Store sensitive data in `.env` file:

```
GOOGLE_CALENDAR_ID=your_calendar_id
OPENAI_API_KEY=your_api_key
```

Copy from `.env.example` and fill in your values.

---

## 📖 Documentation Guide

Read in this order:

1. **README.md** - Project overview ✅
2. **PYTHON_311_SETUP.md** - Python 3.11.9 installation ✅
3. **VOICE_QUICK_START.md** - Quick reference
4. **ENHANCED_FEATURES.md** - Feature documentation
5. **DEVELOPER_GUIDE.md** - Technical details
6. **DOCUMENTATION_INDEX.md** - Full index

---

## 🧩 Key Files Explained

| File | Purpose | Key Functions |
|------|---------|----------------|
| `voice_assistant_calendar.py` | Main app | authenticate(), display_events(), main() |
| `voice_handler.py` | Voice I/O | VoiceRecognizer, VoiceOutput, VoiceCommandParser |
| `book.py` | Booking logic | add_event_to_calendar() |
| `view.py` | Display logic | get_upcoming_events() |
| `gui_dashboard.py` | GUI | CalendarDashboard class (Tkinter) |
| `web_app.py` | Web interface | Flask routes |
| `ai_chatgpt.py` | AI features | ChatGPT integration |
| `requirements-voice.txt` | Dependencies | All Python packages |

---

## ⚙️ System Requirements

- **Python:** 3.11.9 ✅
- **OS:** Windows, macOS, or Linux
- **Microphone:** (optional, for voice features)
- **Internet:** Required for Google APIs
- **RAM:** 200-300 MB
- **Disk Space:** 100 MB

---

## 🚨 Common Issues & Solutions

### Issue: "ModuleNotFoundError"
**Solution:** Activate virtual environment
```powershell
.\venv\Scripts\Activate.ps1
```

### Issue: "pyaudio failed"
**Solution:** Install pre-built wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

### Issue: "tkinter not found"
**Solution:** Reinstall Python 3.11.9 and select "tcl/tk and IDLE"

### Issue: "Google API authentication fails"
**Solution:** Delete `.config/token.json` and re-authenticate

### Issue: "Microphone not working"
**Solution:** Check Windows Sound settings, ensure microphone is default input device

---

## 📊 Project Statistics

- **Lines of Code:** 2000+
- **Lines of Documentation:** 3000+
- **Test Cases:** 38 (100% passing)
- **Voice Commands:** 8+ types
- **Features:** 12+ major features
- **Python Modules:** 8 core files
- **Dependencies:** 15+ packages

---

## 🎯 Next Steps

1. ✅ **Setup Complete** - Python 3.11.9 installed
2. ✅ **Environment Ready** - Virtual environment created
3. ✅ **Dependencies Installed** - All packages ready
4. 🚀 **Run Application** - Start with GUI mode
5. 🎤 **Try Voice Commands** - Book an event using voice
6. 🧪 **Run Tests** - Verify everything works
7. 📖 **Read Documentation** - Deep dive into features

---

## 💡 Usage Tips

### GUI Mode Benefits
- ✅ Visual interface
- ✅ Click buttons or use voice
- ✅ See calendar events
- ✅ Adjust voice settings
- ✅ Best for beginners

### Voice Mode Benefits
- ✅ Completely hands-free
- ✅ Fastest for experienced users
- ✅ Natural language input
- ✅ Voice confirmations

### Text Mode Benefits
- ✅ No microphone needed
- ✅ Quiet environment friendly
- ✅ Precise input

---

## 🔐 Security Notes

✅ HTTPS-only for APIs
✅ No local audio storage
✅ API credentials protected
✅ OAuth 2.0 authentication
✅ Token auto-refresh

---

## 📞 Support

| Resource | Link |
|----------|------|
| GitHub | https://github.com/MLNdlovu/VOICE-ASSISSTANT-CALENDAR |
| Issues | GitHub Issues page |
| Docs | See DOCUMENTATION_INDEX.md |
| Quick Help | COMMANDS_QUICK_REFERENCE.txt |

---

## 🎉 You're Ready!

Your environment is set up and ready to go. Start with:

```powershell
.\venv\Scripts\Activate.ps1
python voice_assistant_calendar.py
```

Select **gui** mode and start exploring! 🚀

---

**Last Updated:** November 13, 2025
**Python Version:** 3.11.9
**Status:** ✅ Production Ready
