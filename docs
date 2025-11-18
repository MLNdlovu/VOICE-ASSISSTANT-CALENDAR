# Accessibility Features Guide - Voice Assistant Calendar

## 🎯 Overview

The Voice Assistant Calendar now includes **comprehensive accessibility features** for visually impaired users. The system provides **automatic audio feedback (text-to-speech)** for all voice commands, making the application fully usable without screen reading.

## 📢 Audio Feedback (Text-to-Speech)

### Web Dashboard Features

When you use the web interface, the system **automatically speaks back** all responses:

#### 1. **Book Meeting Command**
```
User speaks: "Book meeting with John on March 20 at 10 AM"
System speaks: "Meeting booked successfully. Meeting with John on March 20 at 10 AM"
```

#### 2. **Cancel Meeting Command**
```
User speaks: "Cancel meeting on March 20 at 10 AM"
System speaks: "Meeting cancelled successfully on March 20 at 10 AM"
```

#### 3. **View Events Command**
```
User speaks: "Show my events"
System speaks: "You have 3 upcoming events. First event: Team Meeting"
```

#### 4. **Help Command**
```
User speaks: "Help"
System speaks: "Available commands are: book a meeting, cancel a booking, view events, help, share calendar, and config. Say any of these commands to get started."
```

#### 5. **Share Calendar Command**
```
User speaks: "Share calendar"
System speaks: "To share your calendar, go to Google Calendar settings, select your calendar, and add collaborator emails."
```

#### 6. **Error Feedback**
- Missing information: *"Please enter or speak a command"*
- Unknown commands: *"Unknown command. Please try saying: book a meeting, cancel a booking, view events, get help, or share calendar"*
- System errors: *"An error occurred. Please try again."*

### How Audio Feedback Works

The system uses **Web Speech API Text-to-Speech** (built into modern browsers):

1. **Voice Input**: Speak your command into the microphone
2. **Processing**: System processes the command
3. **Audio Response**: System **automatically speaks the result**
4. **Visual Display**: Response also appears on screen for sighted users

## 🌐 Browser Compatibility

| Browser | Voice Input (Speech Recognition) | Audio Output (Text-to-Speech) | Status |
|---------|-----------------------------------|-------------------------------|--------|
| Chrome/Chromium | ✅ Yes | ✅ Yes | **Fully Supported** |
| Microsoft Edge | ✅ Yes | ✅ Yes | **Fully Supported** |
| Firefox | ❌ No (fallback to typing) | ✅ Yes | **Partial** |
| Safari | ❌ No (fallback to typing) | ✅ Yes | **Partial** |
| Opera | ✅ Yes | ✅ Yes | **Fully Supported** |

**Note**: Even if your browser doesn't support speech recognition, you can type commands and still receive audio feedback.

## 🚀 Getting Started

### Step 1: Open Web Dashboard
1. Start the web server: `python web_app.py`
2. Open browser: http://localhost:5000
3. Log in with your Google account

### Step 2: Access Voice Commands Tab
1. Click **"🎤 Voice Commands"** tab (appears first on dashboard)
2. Click **"Start Recording"** button
3. Your browser will ask for microphone permission → **Click "Allow"**

### Step 3: Speak a Command
Try these example commands:

**Book a meeting:**
- "Book meeting on March 20 at 10 AM"
- "Book doctor appointment tomorrow at 2 PM"
- "Book team meeting titled sync with Mike on Friday at 3 PM"

**Cancel a meeting:**
- "Cancel meeting on March 20 at 10 AM"
- "Cancel appointment tomorrow at 2 PM"

**View events:**
- "Show my events"
- "What's on my calendar"
- "List upcoming meetings"

**Get help:**
- "Help"
- "What commands can I use"

### Step 4: Listen to Feedback
The system will **automatically speak** the result:
- ✅ Success: *"Meeting booked successfully..."*
- ❌ Error: *"Failed to create meeting. Please try again..."*

## 🎙️ Advanced Voice Commands

### Date/Time Formats Supported
The system understands natural language dates:
- "March 20" or "20 March"
- "Tomorrow", "Next Monday", "Friday"
- "10 AM", "2:30 PM", "14:00"
- "Today at 3 PM", "Next week on Wednesday"

### Examples:
```
"Book meeting on 23 March 2026 at 10:00"
"Cancel appointment tomorrow at 2 PM"
"Book conference call Friday at 3 PM"
"Show all events next week"
```

## 💻 CLI Voice Mode

The command-line interface also supports audio feedback:

### Launch CLI with Voice Input
```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the app
python voice_assistant_calendar.py

# When prompted, choose "2. CLI - Voice input"
```

### CLI Commands with Audio Feedback
All CLI commands also provide audio responses:

```
User speaks: "book meeting on March 20 at 10 AM"
System speaks: "Meeting booked successfully. Meeting on March 20 at 10 AM"
System displays: ✅ Meeting booked successfully: Meeting on March 20 at 10:00+02:00
```

## 🔧 Customizing Audio Settings

### Adjust Speech Speed
The system speaks at **0.9x speed** for clarity (slightly slower than normal).

To change this, edit `static/app.js`:
```javascript
utterance.rate = 0.9;  // Change to 0.8 for slower, 1.0 for normal speed
```

### Choose Voice
Modern browsers allow you to select different voices:
```javascript
utterance.voice = speechSynthesis.getVoices()[0];  // Select different voice
```

### Adjust Volume
```javascript
utterance.volume = 1.0;  // Range: 0 to 1
```

## 🧪 Testing Accessibility Features

### Test Checklist
- [ ] Web dashboard loads without errors
- [ ] Click "🎤 Voice Commands" tab
- [ ] Click "Start Recording" button
- [ ] Speak: "Help"
- [ ] System speaks back: "Available commands are..."
- [ ] Speak: "Book meeting on March 20 at 10 AM"
- [ ] System speaks: "Meeting booked successfully..."
- [ ] Close browser and restart (test persistence)

### Voice Commands Test Suite
```
✅ Test 1: Book meeting
   Say: "book meeting tomorrow at 2 PM"
   Expected: Audio response + visual confirmation

✅ Test 2: Cancel meeting
   Say: "cancel meeting tomorrow at 2 PM"
   Expected: Audio response + visual confirmation

✅ Test 3: View events
   Say: "show my events"
   Expected: List of events read aloud

✅ Test 4: Get help
   Say: "help"
   Expected: Audio explanation of available commands

✅ Test 5: Error handling
   Say: "unknown command xyz"
   Expected: Error message spoken: "Unknown command..."
```

## 🐛 Troubleshooting

### Microphone Not Working
1. Check browser permissions: Settings → Privacy → Microphone
2. Ensure microphone is connected and working
3. Try refreshing the page
4. Try typing commands instead (fallback to typing)

### Audio Not Playing
1. Check browser volume is not muted
2. Check system volume is up
3. Try a different browser (Chrome/Edge recommended)
4. Check that speakers/headphones are connected

### Commands Not Recognized
1. Speak clearly and naturally
2. Wait for "Listening..." indicator
3. Try simpler commands: "help", "events"
4. Use the text input instead for precise control

### Slow Speech Response
1. Use Chrome or Edge for best performance
2. Reduce background noise
3. Close other browser tabs using audio
4. Check internet connection

## 📱 Mobile Accessibility

### iOS/Safari
- Fallback to text input (speech recognition not available)
- Audio feedback works in Safari
- Tap "Voice Commands" tab → type command → audio response

### Android/Chrome
- Full support for voice input
- Audio feedback available
- Same experience as desktop

## ♿ WCAG Compliance

This implementation supports:
- ✅ **WCAG 2.1 Level AA** for voice input
- ✅ **Screen reader compatible** (audio feedback doesn't conflict)
- ✅ **Keyboard accessible** (can use Tab/Enter)
- ✅ **Color contrast** for visual feedback
- ✅ **No flashing/seizure triggers** (safe for photosensitive users)

## 🎓 Educational Features

### For Instructors/Administrators
The accessibility features demonstrate:
1. **Web Speech API usage** for voice I/O
2. **Asynchronous command processing** with feedback
3. **Universal design** principles
4. **Progressive enhancement** (works without microphone)

### Code Reference
- **Frontend**: `static/app.js` - `speakText()` function
- **Backend**: `web_app.py` - `/api/voice` endpoint with `speak_text` responses
- **CLI**: `voice_assistant_calendar.py` - `voice_handler.speak()` calls

## 🚀 Future Enhancements

Planned accessibility improvements:
- [ ] Google Cloud Speech-to-Text fallback (more languages)
- [ ] Custom voice selection per user
- [ ] Command history playback
- [ ] Haptic feedback for mobile devices
- [ ] Real-time transcription display
- [ ] Command confirmation before execution
- [ ] Multi-language support

## 📞 Support

For accessibility issues or suggestions:
1. Test in Chrome/Edge first (best support)
2. Check browser microphone permissions
3. Review browser console for error messages
4. Try the text input fallback
5. Report specific error messages

## 📚 Additional Resources

- [Web Speech API Documentation](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Accessible Web Design](https://www.w3.org/WAI/)
- [Voice UI Best Practices](https://www.nngroup.com/articles/voice-user-interfaces/)

---

**Last Updated**: November 2025
**Status**: ✅ Production Ready
**Tested On**: Chrome 120+, Edge 120+, Firefox 121+, Safari 17+

