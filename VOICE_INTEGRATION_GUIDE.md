# Voice Command Integration Guide

## Overview

The Voice Assistant Calendar application now includes client-side voice command integration using the Web Speech API for browsers (SpeechRecognition + speechSynthesis) and the `SpeechRecognition`/`pyttsx3` stack for local/CLI usage. This enables users — including visually impaired users — to control the app with natural language and receive spoken feedback from the browser or the local CLI.

## Features

### 🎤 Voice Input Capabilities

1. **Speech Recognition**: Converts spoken words to text using Google's Speech Recognition API
2. **Natural Language Parsing**: Extracts commands and parameters from conversational speech
3. **Fallback Support**: Automatically falls back to text input if voice is unavailable
4. **Error Handling**: Graceful degradation with helpful error messages

### Supported Voice Commands

#### 1. **Book a Slot**
```
"Book a slot on 2024-03-01 at 10:00 for Python help"
"Schedule a session on March 1st at 10 AM studying algorithms"
"I want to book a clinic for data structures at 2:30 PM today"
```
Extracts: date, time, and topic/summary

#### 2. **Cancel a Booking**
```
"Cancel my booking on 2024-03-01 at 10:00"
"Cancel the session on March 1st at 10 AM"
"Unbook my appointment for today at 2 PM"
```
Extracts: date and time

#### 3. **View Events**
```
"Show me upcoming events"
"View my events"
"List upcoming events"
"What are my events?"
```

#### 4. **View Calendar**
```
"Show me the calendar"
"Open my calendar"
"List my upcoming events"
"Show calendar events"
```

#### 5. **Share Calendar**
```
"Share my calendar"
"How do I share my calendar?"
"Show calendar sharing instructions"
```

#### 6. **Help**
```
"Help"
"What can I do?"
"Show available commands"
```

#### 7. **Configuration**
```
"Config"
"Configure"
"Authenticate"
"Login"
```

#### 8. **Exit**
```
"Exit"
"Quit"
"Goodbye"
"Bye"
```

## Installation

### Prerequisites

- Python 3.7+
- Microphone device
- Internet connection (for Google Speech Recognition API)

### Step 1: Install Required Packages

```bash
pip install SpeechRecognition pyaudio google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

**Platform-Specific Notes:**

**Windows:**
```bash
pip install SpeechRecognition pyaudio
```

**macOS:**
```bash
brew install portaudio
pip install SpeechRecognition pyaudio
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install portaudio19-dev
pip install SpeechRecognition pyaudio
```

### Step 2: Verify Installation

Test voice recognition availability:
```bash
python voice_handler.py
```

Expected output:
```
Voice Command Integration Test
============================================================

1. Testing VoiceCommandParser:
...
2. Testing VoiceRecognizer availability:
============================================================
Voice recognition available: True
```

## Usage

### Running the Application with Voice Support

```bash
python voice_assistant_calendar.py
```

### Interactive Input Selection

When you run the application, you'll be prompted to choose your input method:

```
============================================================
Choose Input Method:
============================================================
1. Voice input (requires microphone)
2. Text input
Type 'voice' or 'text' (default: text): 
```

### Example Voice Session

**1. Start the application:**
```bash
python voice_assistant_calendar.py
```

**2. Choose voice input:**
```
Type 'voice' or 'text' (default: text): voice
```

**3. Speak your command:**
```
🎤 Listening for command (speak now)...
```
*Say: "Book a slot on 2024-03-01 at 10:00 for Python help"*

**4. System processes and confirms:**
```
✅ Heard: "book a slot on 2024-03-01 at 10:00 for python help"
📋 Parsed command: book
   Parameters: {'date': '2024-03-01', 'time': '10:00', 'summary': 'python help'}
```

**5. Complete the booking:**
The system may ask for additional information (email, etc.) if not captured from voice.

## Module Architecture

### `voice_handler.py`

Main voice integration module with three key components:

#### 1. **VoiceRecognizer Class**
```python
recognizer = VoiceRecognizer(timeout=15, phrase_time_limit=15)
text = recognizer.listen()
```

Methods:
- `is_available()`: Check if voice recognition is working
- `listen(prompt)`: Listen to microphone and return recognized text

#### 2. **VoiceCommandParser Class**
```python
command, params = VoiceCommandParser.parse_command(text)
```

Methods:
- `parse_command(text)`: Converts text to structured command
- `extract_datetime(text)`: Extracts date and time
- `extract_summary(text)`: Extracts topic/summary
- `_match_pattern(text, patterns)`: Pattern matching utility

#### 3. **Main Pipeline Function**
```python
command, params = voice_handler.get_voice_command()
```

## Command Flow Diagram

```
┌─────────────────────────────┐
│   Start Application         │
└──────────────┬──────────────┘
               │
        ┌──────▼──────┐
        │ Choose Input│
        └──────┬──────┘
         Voice│ Text
            ┌─┴─────────────┐
            ▼               ▼
      ┌──────────┐   ┌────────────┐
      │Recognize │   │Text Input  │
      │Speech    │   │from user   │
      └──────┬───┘   └───────┬────┘
            │                │
            └────────┬───────┘
                     │
              ┌──────▼──────┐
              │Parse Command│
              │Extract Params│
              └──────┬──────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
      ┌─────────┐        ┌───────────┐
      │Known    │        │Unknown    │
      │Command  │        │Command    │
      └────┬────┘        └─────┬─────┘
           │                   │
        Execute         Ask for retry
           │             or text input
           ▼
      ┌──────────────┐
      │ Complete Task│
      └──────────────┘
```

## Error Handling

The voice system handles several error scenarios:

### 1. **Microphone Not Available**
```
⚠️  Microphone initialization failed: [error details]
```
**Solution**: Check microphone connection or install pyaudio

### 2. **No Speech Detected**
```
⏱️  No speech detected (timeout).
```
**Solution**: Speak louder or move closer to microphone

### 3. **Audio Quality Issues**
```
❌ Sorry, could not understand audio. Please try again.
```
**Solution**: Reduce background noise or re-try

### 4. **Network Issues**
```
❌ Speech recognition failed: [error details]
```
**Solution**: Check internet connection (required for Google API)

### 5. **Command Not Recognized**
```
⚠️  Could not parse command. Please use text input instead.
```
**Solution**: Use simpler, more direct language

## Troubleshooting

### Issue: "speech_recognition not installed"

**Solution:**
```bash
pip install SpeechRecognition
```

### Issue: "No module named 'pyaudio'"

**Solution:**

Windows:
```bash
pip install pipwin
pipwin install pyaudio
```

macOS:
```bash
brew install portaudio
pip install pyaudio
```

Linux:
```bash
sudo apt-get install portaudio19-dev python3-dev
pip install pyaudio
```

### Issue: "Speech recognition request failed"

This typically means no internet connection. Ensure you're connected to the internet.

### Issue: Microphone not being detected

**Solutions:**
1. Check system sound settings
2. Try a different microphone
3. Update audio drivers
4. Run as administrator (Windows)

## Advanced Usage

### Custom Timeout Settings

```python
from voice_handler import VoiceRecognizer

recognizer = VoiceRecognizer(timeout=10, phrase_time_limit=8)
text = recognizer.listen("Please speak your command...")
```

### Direct Parser Usage

```python
from voice_handler import VoiceCommandParser

parser = VoiceCommandParser()
command, params = parser.parse_command(
    "Book a slot on 2024-03-01 at 10:00 for Python"
)
print(command)  # 'book'
print(params)   # {'date': '2024-03-01', 'time': '10:00', 'summary': 'Python'}
```

### Batch Processing

```python
from voice_handler import VoiceCommandParser

commands = [
    "Book a slot on 2024-03-01 at 10:00 for Python help",
    "Cancel my booking on 2024-03-01 at 10:00",
    "Show me upcoming events",
]

parser = VoiceCommandParser()
for cmd_text in commands:
    command, params = parser.parse_command(cmd_text)
    print(f"Command: {command}, Params: {params}")
```

## Performance Considerations

1. **First-time Setup**: Speech recognition initialization takes ~1-2 seconds
2. **Audio Processing**: Depends on internet speed and audio quality (typically 1-3 seconds)
3. **Command Parsing**: Instant (<100ms)
4. **Microphone Adjustment**: ~0.5 seconds (automatic)

## Privacy & Security

- **Audio Data**: Speech audio is sent to Google's servers for recognition
- **No Recording**: Audio is not stored locally; it's streamed and deleted after recognition
- **HTTPS**: All communication is encrypted
- **Rate Limiting**: Google has rate limits on the free API (consider alternatives for production)

## Limitations

1. **Internet Required**: Google Speech Recognition API requires internet connectivity
2. **Accents**: Recognition accuracy varies by accent and language
3. **Background Noise**: Noisy environments reduce accuracy
4. **Date Parsing**: Relative dates (e.g., "tomorrow", "next Monday") may need enhancement
5. **Free API Limits**: Google's free API has usage limits

## Future Enhancements

- [ ] Support for offline speech recognition (e.g., DeepSpeech)
- [ ] Support for multiple languages
- [ ] Relative date parsing ("tomorrow", "next week")
- [ ] Multi-turn conversations
- [ ] Voice feedback confirmation
- [ ] Command history
- [ ] Custom voice commands configuration

## Testing

Run the test suite:

```bash
python -m pytest tests/ -v
```

Test voice functionality:

```bash
python voice_handler.py
```

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review error messages and stack traces
3. Test microphone separately: `python voice_handler.py`
4. Try text input as a fallback

## References

- [SpeechRecognition Library](https://github.com/Uberi/speech_recognition)
- [Google Speech Recognition API](https://cloud.google.com/speech-to-text)
- [PyAudio Documentation](https://people.csail.mit.edu/hubert/pyaudio/)
