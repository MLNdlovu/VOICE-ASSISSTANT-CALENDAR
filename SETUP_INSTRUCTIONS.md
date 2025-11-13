# 🚀 Voice Assistant Calendar - Setup Instructions for Work Computer

## Quick Setup (5 minutes)

### 1. Clone the Repository
```bash
git clone https://github.com/MLNdlovu/VOICE-ASSISSTANT-CALENDAR.git
cd VOICE-ASSISSTANT-CALENDAR
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements-voice.txt
```

### 4. Verify Installation
```bash
python -c "import pyttsx3; print('✓ Text-to-speech OK')"
python -c "import speech_recognition; print('✓ Voice recognition OK')"
python -c "import tkinter; print('✓ GUI OK')"
```

### 5. Run the Application
```bash
python voice_assistant_calendar.py
```

When prompted, choose your interface:
- **gui** - Graphical interface (recommended)
- **voice** - Voice commands only
- **text** - Text input only

---

## Detailed Setup Guide

### Prerequisites
- **Python 3.7+** (check with `python --version`)
- **Git** (check with `git --version`)
- **Microphone** (for voice features)
- **Internet connection** (for Google Calendar API)

### Step-by-Step Installation

#### Step 1: Clone Repository
```bash
# Navigate to your desired directory
cd C:\Users\YourUsername\Documents

# Clone the project
git clone https://github.com/MLNdlovu/VOICE-ASSISSTANT-CALENDAR.git
cd VOICE-ASSISSTANT-CALENDAR
```

#### Step 2: Virtual Environment Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.\.venv\Scripts\activate

# macOS/Linux:
source .venv/bin/activate
```

You should see `(.venv)` prefix in your terminal after activation.

#### Step 3: Install Requirements
```bash
# Install all dependencies
pip install -r requirements-voice.txt

# This installs:
# - google-auth-oauthlib==1.2.0
# - google-api-python-client==2.104.0
# - prettytable==3.10.0
# - SpeechRecognition==3.10.1
# - pyaudio==0.2.13
# - pyttsx3==2.90
# - pytest==7.4.3
# - pytest-cov==4.1.0
```

**If you get PyAudio errors on Windows:**
```bash
# Download pre-built wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
# Then install:
pip install path/to/pyaudio_whl_file.whl
```

#### Step 4: Google Calendar Setup
1. Go to: https://console.cloud.google.com
2. Create a new project
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials JSON
6. Place it in `.config/client_secret_*.json`

Or use existing credentials if already configured.

#### Step 5: Verify Installation
```bash
# Test each component
python -c "import google.oauth2; print('✓ Google OAuth')"
python -c "import pyttsx3; print('✓ Text-to-Speech')"
python -c "import speech_recognition; print('✓ Voice Recognition')"
python -c "import tkinter; print('✓ GUI')"
python -c "import pytest; print('✓ Testing')"
```

---

## Running the Application

### GUI Mode (Recommended)
```bash
python voice_assistant_calendar.py
```
Then select **gui** when prompted.

**GUI Features:**
- View next 7 calendar events
- Add events (text or voice)
- Cancel bookings
- Adjust voice settings
- Built-in help

### Voice Mode
```bash
python voice_assistant_calendar.py
```
Then select **voice** when prompted.

**Voice Commands:**
- "Book tomorrow at 2 PM for Python help"
- "Show me upcoming events"
- "Cancel my booking on 2024-03-15 at 10:00"
- "Help"

### Text Mode
```bash
python voice_assistant_calendar.py
```
Then select **text** when prompted.

---

## Running Demo

See all features in action:
```bash
python enhanced_features_demo.py
```

This demonstrates:
- Voice output (text-to-speech)
- NLP parsing with relative dates
- DateTime extraction
- Realistic usage scenarios

---

## Running Tests

Run all 38 tests:
```bash
pytest tests/test_voice_commands.py -v
```

Run specific test class:
```bash
pytest tests/test_voice_commands.py::TestRelativeDateParsing -v
```

With coverage report:
```bash
pytest tests/test_voice_commands.py --cov=voice_handler --cov-report=html
```

---

## Example Voice Commands

### Booking Events
```
"Book tomorrow at 2:30 PM for Python help"
"Schedule in 3 days at 10:00 for database design"
"Book next Monday at 14:00 for interview prep"
"Schedule on 2024-03-20 at 10:00 for SQL training"
```

### Viewing Calendar
```
"Show me upcoming events"
"View code clinics calendar"
"List all events"
```

### Canceling Events
```
"Cancel my booking on 2024-03-15 at 10:00"
"Unbook my appointment on tomorrow at 14:00"
```

### Other Commands
```
"Help"
"Settings"
"Exit"
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'pyttsx3'"
**Solution:**
```bash
pip install pyttsx3
```

### Issue: "No microphone found"
**Solution:**
- Check audio input devices in Windows Settings
- Ensure microphone is plugged in and enabled
- Test with: `python -c "import speech_recognition as sr; sr.Microphone().list_microphone_indexes()"`

### Issue: "Google Calendar authentication fails"
**Solution:**
1. Delete `.config/token.json` (cached token)
2. Re-run application to re-authenticate
3. Follow browser OAuth flow

### Issue: "PyAudio installation fails on Windows"
**Solution:**
```bash
# Option 1: Install pre-built wheel
# Download from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
pip install path/to/pyaudio_wheel.whl

# Option 2: Skip PyAudio (use voice without audio input)
# Edit requirements-voice.txt and comment out pyaudio line
```

### Issue: "tkinter not found"
**Solution:**
- **Windows:** tkinter comes with Python. Reinstall Python and select "tcl/tk and IDLE"
- **macOS:** `brew install python-tk`
- **Linux:** `sudo apt-get install python3-tk`

---

## Project Structure

```
VOICE-ASSISSTANT-CALENDAR/
├── voice_assistant_calendar.py    # Main application
├── voice_handler.py               # Voice I/O & NLP
├── gui_dashboard.py               # GUI interface
├── book.py                        # Booking logic
├── view.py                        # Calendar display
├── get_details.py                 # Input utilities
├── tests/
│   └── test_voice_commands.py     # Test suite (38 tests)
├── .config/                       # Google OAuth config
├── requirements-voice.txt         # Dependencies
├── ENHANCED_FEATURES.md           # Feature documentation
├── VOICE_QUICK_START.md           # Quick reference
├── DEVELOPER_GUIDE.md             # Developer documentation
└── enhanced_features_demo.py      # Interactive demo
```

---

## Documentation

Start with these docs in order:

1. **README.md** - Project overview
2. **VOICE_QUICK_START.md** - Quick reference guide
3. **ENHANCED_FEATURES.md** - Complete feature guide
4. **DEVELOPER_GUIDE.md** - Technical details
5. **DOCUMENTATION_INDEX.md** - Full index

---

## Key Features

✅ **Voice Input** - Speech recognition with Google API
✅ **Voice Output** - Text-to-speech with adjustable rate & volume
✅ **Natural Language** - Relative dates (tomorrow, in 3 days, next Monday)
✅ **GUI Dashboard** - Modern Tkinter interface
✅ **Calendar Integration** - Google Calendar API
✅ **Comprehensive Tests** - 38 tests (100% passing)
✅ **Full Documentation** - 2000+ lines of docs

---

## First Run Checklist

- [ ] Repository cloned
- [ ] Virtual environment created and activated
- [ ] Dependencies installed
- [ ] Google Calendar configured
- [ ] Installation verified (all 5 components working)
- [ ] Demo ran successfully
- [ ] Application started without errors
- [ ] Tests passing (38/38)

---

## Next Steps

1. **Explore the GUI:**
   ```bash
   python voice_assistant_calendar.py
   # Select: gui
   ```

2. **Try voice commands:**
   - Click "🎤 Add Event (Voice)"
   - Say: "Book tomorrow at 2 PM for Python help"

3. **Check documentation:**
   - Open `ENHANCED_FEATURES.md`
   - Review `VOICE_QUICK_START.md`

4. **Run tests:**
   ```bash
   pytest tests/test_voice_commands.py -v
   ```

5. **Explore code:**
   - `voice_handler.py` - Voice engine
   - `gui_dashboard.py` - GUI implementation
   - `book.py` - Booking logic

---

## Support & Resources

| Resource | Location |
|----------|----------|
| GitHub Repo | https://github.com/MLNdlovu/VOICE-ASSISSTANT-CALENDAR |
| Full Docs | `DOCUMENTATION_INDEX.md` |
| Quick Start | `VOICE_QUICK_START.md` |
| Features | `ENHANCED_FEATURES.md` |
| Dev Guide | `DEVELOPER_GUIDE.md` |
| Demo | `enhanced_features_demo.py` |

---

## Command Cheat Sheet

```bash
# Activate environment
.\.venv\Scripts\activate

# Run application
python voice_assistant_calendar.py

# Run demo
python enhanced_features_demo.py

# Run tests
pytest tests/test_voice_commands.py -v

# Run with coverage
pytest tests/test_voice_commands.py --cov=voice_handler

# Pull latest changes
git pull origin main

# Check Python version
python --version

# Check installed packages
pip list

# Upgrade pip
python -m pip install --upgrade pip
```

---

**Status:** ✅ Production Ready
**Version:** 2.0 (Enhanced Edition)
**Last Updated:** November 13, 2025

Happy coding! 🚀
