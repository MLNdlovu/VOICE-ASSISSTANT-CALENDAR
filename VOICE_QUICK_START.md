# Voice Command Integration - Quick Start Guide

## 🎯 Quick Start (5 Minutes)

### 1. Install Voice Dependencies

```bash
pip install -r requirements-voice.txt
```

Or install manually:
```bash
pip install SpeechRecognition pyaudio google-api-python-client google-auth-oauthlib
```

### 2. Test Voice Recognition Setup

```bash
python voice_handler.py
```

Expected output:
```
Voice recognition available: True
```

### 3. Run the Application

```bash
python code_clinics_demo.py
```

### 4. Choose Voice Input

When prompted:
```
Choose Input Method:
Type 'voice' or 'text' (default: text): voice
```

### 5. Speak Your Command

Examples:
- "Book a slot on 2024-03-01 at 10:00 for Python"
- "Show me upcoming events"
- "Cancel my booking on 2024-03-01 at 10:00"

---

## 📋 Command Examples

### Booking a Slot
```
"Book a slot on March 1st at 10 AM for Python help"
"I want to book a code clinic session at 2:30 PM for algorithms"
```

### Canceling a Booking
```
"Cancel my booking on 2024-03-01 at 10:00"
"Unbook my appointment at 2 PM"
```

### Viewing Events
```
"Show me my upcoming events"
"List code clinic slots"
```

---

## 🔧 Troubleshooting

### Microphone Not Working?

**Windows:**
```bash
pip install pipwin
pipwin install pyaudio
```

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Linux:**
```bash
sudo apt-get install portaudio19-dev
pip install pyaudio
```

### "No module named 'speech_recognition'"?
```bash
pip install SpeechRecognition
```

### Speech Not Recognized?
- Speak clearly and loudly
- Reduce background noise
- Check microphone is selected in system settings
- Try text input instead (press Enter when prompted)

---

## 🎤 Voice Input Flow

```
1. Application prompts for input method
   ↓
2. You choose "voice"
   ↓
3. System listens: "Listening for command..."
   ↓
4. You speak: "Book a slot on 2024-03-01 at 10:00 for Python"
   ↓
5. System processes: "Heard: book a slot..."
   ↓
6. Command parsed: "Parsed command: book"
   ↓
7. Complete booking
```

---

## ✨ Key Features

✅ **Hands-Free Operation** - No typing needed  
✅ **Natural Language** - Speak conversationally  
✅ **Error Handling** - Graceful fallback to text  
✅ **Smart Parsing** - Extracts dates, times, topics  
✅ **Cross-Platform** - Works on Windows, macOS, Linux  

---

## 📚 Learn More

- Full documentation: `VOICE_INTEGRATION_GUIDE.md`
- Test suite: `tests/test_voice_commands.py`
- Source code: `voice_handler.py`

---

## 💡 Tips

1. **Exact Dates Help**: Say "2024-03-01" instead of "next Friday"
2. **Speak Clearly**: Enunciate to improve recognition
3. **Reduce Noise**: Use voice in quiet environments
4. **Try Text First**: Get familiar with command structure in text mode first

---

## 🚀 Next Steps

1. Run the application: `python web_app.py`
2. Try a few voice commands
3. Refer to `VOICE_INTEGRATION_GUIDE.md` for advanced usage
4. Run tests: `pytest tests/test_voice_commands.py`

Enjoy hands-free calendar management! 🎉
