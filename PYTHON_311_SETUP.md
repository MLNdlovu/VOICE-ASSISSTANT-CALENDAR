# Python 3.11.9 Setup Guide

## Quick Setup Instructions

### Step 1: Download Python 3.11.9

1. Go to: https://www.python.org/downloads/release/python-3119/
2. Download the **Windows installer (64-bit)** for your system
3. **IMPORTANT:** When installing, check "Add Python to PATH"

### Step 2: Verify Python Installation

Open PowerShell and run:
```powershell
python --version
```

Should output: `Python 3.11.9`

### Step 3: Navigate to Project Directory

```powershell
cd "C:\Users\User\Documents\dbn_12_code_clinics-master"
```

### Step 4: Create Virtual Environment

```powershell
python -m venv venv
```

This creates a `venv` folder in your project directory.

### Step 5: Activate Virtual Environment

```powershell
.\venv\Scripts\Activate.ps1
```

You should see `(venv)` at the beginning of your PowerShell prompt.

**Note:** If you get an execution policy error, run this first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 6: Upgrade pip

```powershell
python -m pip install --upgrade pip
```

### Step 7: Install Dependencies

```powershell
pip install -r requirements-voice.txt
```

This will install all required packages including:
- Google Calendar API
- Speech Recognition
- Text-to-Speech (pyttsx3)
- GUI components (tkcalendar)
- Testing framework (pytest)
- Flask for web dashboard
- OpenAI for AI features

### Step 8: Verify Installation

Test that all key components are working:

```powershell
# Test Google API
python -c "from google.oauth2 import service_account; print('✓ Google OAuth')"

# Test Text-to-Speech
python -c "import pyttsx3; print('✓ Text-to-Speech')"

# Test Voice Recognition
python -c "import speech_recognition; print('✓ Voice Recognition')"

# Test GUI
python -c "import tkinter; print('✓ GUI/Tkinter')"

# Test Testing framework
python -c "import pytest; print('✓ Pytest')"
```

All should show checkmarks (✓).

---

## Running the Application

Make sure virtual environment is activated: `(venv)` should be visible in prompt.

### Option 1: GUI Mode (Recommended)
```powershell
python voice_assistant_calendar.py
```
Select `gui` when prompted.

### Option 2: Voice Mode
```powershell
python voice_assistant_calendar.py
```
Select `voice` when prompted.

### Option 3: Text Mode
```powershell
python voice_assistant_calendar.py
```
Select `text` when prompted.

---

## Running Tests

```powershell
# Run all tests with verbose output
pytest tests/test_voice_commands.py -v

# Run specific test class
pytest tests/test_voice_commands.py::TestRelativeDateParsing -v

# Run with coverage report
pytest tests/test_voice_commands.py --cov=voice_handler --cov-report=html
```

---

## Running the Demo

```powershell
python enhanced_features_demo.py
```

---

## Deactivating Virtual Environment

When done working, deactivate the environment:

```powershell
deactivate
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError" when running application

**Solution:** Make sure virtual environment is activated (you should see `(venv)` in your prompt)

```powershell
# Check if activated
Get-Content env:VIRTUAL_ENV

# If empty, activate it
.\venv\Scripts\Activate.ps1
```

### Issue: "PyAudio failed to install"

**Solution:** Download pre-built wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

Then install:
```powershell
pip install "C:\path\to\pyaudio_wheel.whl"
```

### Issue: "Python is not recognized as an internal command"

**Solution:** Python 3.11.9 wasn't added to PATH during installation. 

Reinstall Python 3.11.9 and make sure to **CHECK** "Add Python to PATH" during installation.

### Issue: "tkinter not found"

**Solution:** Reinstall Python 3.11.9 and select:
- ✅ pip (automatic)
- ✅ tcl/tk and IDLE (must check this!)
- ✅ Add Python to PATH

### Issue: Execution policy error with activate script

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
.\venv\Scripts\Activate.ps1
```

---

## File Structure After Setup

```
dbn_12_code_clinics-master/
├── venv/                          # Virtual environment
├── voice_assistant_calendar.py    # Main application
├── voice_handler.py               # Voice I/O & NLP
├── gui_dashboard.py               # GUI interface
├── book.py                        # Booking logic
├── view.py                        # Calendar display
├── get_details.py                 # Input utilities
├── enhanced_features_demo.py      # Demo script
├── requirements-voice.txt         # Dependencies
├── tests/                         # Test suite
└── .config/                       # Google OAuth config
```

---

## Common Commands

```powershell
# Navigate to project
cd "C:\Users\User\Documents\dbn_12_code_clinics-master"

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run main application
python voice_assistant_calendar.py

# Run tests
pytest tests/test_voice_commands.py -v

# Run demo
python enhanced_features_demo.py

# Install new package
pip install package_name

# List installed packages
pip list

# Deactivate environment
deactivate
```

---

## Verification Checklist

After completing all steps, verify:

- [ ] Python 3.11.9 installed: `python --version`
- [ ] Virtual environment created: `venv` folder exists
- [ ] Virtual environment activated: `(venv)` in prompt
- [ ] Dependencies installed: `pip list` shows all packages
- [ ] All components working: All 5 verification tests pass
- [ ] Application runs: `python voice_assistant_calendar.py` starts without errors
- [ ] Tests pass: `pytest tests/test_voice_commands.py -v` shows passing tests

---

**You're ready to go!** 🚀

Start with:
```powershell
.\venv\Scripts\Activate.ps1
python voice_assistant_calendar.py
```
