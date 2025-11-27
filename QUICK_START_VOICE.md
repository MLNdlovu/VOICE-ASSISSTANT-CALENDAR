# Voice Assistant Quick Start Guide

## 5-Minute Setup

### 1. Get Hugging Face API Key
1. Go to https://huggingface.co/settings/tokens
2. Create a new token (read access)
3. Copy the token

### 2. Configure Environment
Open `.env` and replace:
```
HF_API_KEY=your_actual_huggingface_token_here
FLASK_SECRET=generate-any-random-string-here
```

### 3. Install Dependencies
```bash
pip install -r requirements-voice.txt
```

### 4. Start Server
```bash
python web_app.py
```

You'll see:
```
Starting Voice Assistant Calendar Web Server...
Open http://localhost:5000 in your browser
```

### 5. Access Voice Interface
Open in browser: **http://localhost:5000/voice**

(You must be logged in first - if redirected to login, use existing credentials or register)

---

## First Time Usage

1. **Set Trigger Phrase**
   - Modal appears: "Set Your Voice Trigger"
   - Enter something like: "Hey Voice" or "OK Calendar"
   - Click "Save Trigger"
   - Hear: "Welcome back, I'm ready. Say your trigger to begin."

2. **Say Your Trigger**
   - Status shows: "Say your trigger…"
   - Say exactly what you set (fuzzy match at 75%+)
   - Hear activation tone (ding!)
   - Status changes: "Say your command…"

3. **Give a Command**
   - Examples:
     - "Book a meeting tomorrow at 2 PM called budget review"
     - "Show my events for Friday"
     - "What's on my calendar today?"
   - Wait 2 seconds of silence (auto-submits) or keep talking
   - Assistant responds and speaks back

4. **That's It!**
   - Response disappears after 2 seconds
   - Say your trigger again for next command

---

## Test Commands

Try these to verify everything works:

### Booking
```
"Book a meeting tomorrow at 10 AM called standup"
→ Creates event
→ Response: "I'll book your standup meeting..."
```

### List Events
```
"Show my events"
→ Asks "Which day?"
→ Say "Tomorrow"
→ Shows events in cards
→ Reads: "You have N events..."
```

### General Chat
```
"Hello"
→ Response: "Hi! How can I help you today?"
```

### Error Handling
```
"asdfghjkl"
→ Response: "I couldn't understand that..."
→ Automatically retries
```

---

## Troubleshooting

### "Mic button not responding"
- Check browser permissions (allow microphone)
- Chrome: Settings → Privacy → Microphone
- Firefox: Preferences → Privacy → Permissions

### "Can't hear TTS"
- Check browser volume
- Check system volume
- Make sure speakers/headphones work
- Try typing in Chrome DevTools console: `speechSynthesis.speak(new SpeechSynthesisUtterance("test"))`

### "Speech not recognized"
- Speak clearly and loud enough
- Check for background noise
- Try closer to microphone
- Browser will wait 2+ seconds for speech to end

### "Getting HuggingFace API errors"
- Verify `HF_API_KEY` in `.env` is correct
- Check token has "read" permissions
- Restart server after changing `.env`

### "Trigger not working"
- Must match 75%+ similarity to what you set
- Try saying it slightly differently
- Fuzzy matching is forgiving but not perfect

---

## Tips & Tricks

### Settings (⚙️ button)
- **Speech Rate:** 1.05 is natural, 0.5 is slow, 2.0 is fast
- **Pitch:** 1.0 is normal, <1 is deeper, >1 is higher
- **Always On:** Enable to auto-listen (no button click needed)

### Privacy
- Trigger phrase is NOT shown anywhere
- Stored only in sessionStorage (cleared on tab close)
- Change trigger anytime in settings
- No transcripts saved to server by default

### Events Display
- Shows as small cards for 5 seconds
- Automatically hides
- Spoken summary: "You have 2 events: Event 1 at 9am, Event 2 at 1pm"

### Multi-Turn (Follow-ups)
- If assistant asks a question, just answer
- Backend remembers context for that turn only
- After response, fully resets for next trigger

---

## Common Workflows

### Book a Meeting
```
1. Say trigger: "Hey Voice"
2. Say: "Book a meeting tomorrow at 2 PM called team standup"
3. Hear: "I'll book your team standup meeting for tomorrow at two PM"
4. Done! (event created in calendar)
```

### Check Calendar
```
1. Say trigger: "Hey Voice"
2. Say: "What's on my calendar today"
3. Hear: "You have 3 events: Meeting at 9am, Lunch at 12pm, Review at 3pm"
4. Cards display for 5 seconds showing each event
```

### Change Trigger Phrase
```
1. Click ⚙️ (settings)
2. Click "Change Trigger Phrase"
3. Enter new trigger (e.g., "OK Calendar")
4. Old trigger stops working immediately
5. New trigger starts working
```

### Always-On Listening
```
1. Click ⚙️ (settings)
2. Toggle "Always On"
3. Mic auto-listens without clicking button
4. Just say trigger anytime
```

---

## Architecture Notes

### Frontend
- **Location:** `/voice` route
- **Technology:** HTML5, CSS3, Vanilla JS
- **APIs:** Web Speech API (STT), speechSynthesis (TTS)
- **Storage:** sessionStorage (trigger), localStorage (settings)

### Backend
- **Endpoints:**
  - `POST /api/voice_cmd` - Process commands
  - `POST /api/set_trigger` - Store trigger
  - `GET /api/get_trigger_status` - Check status
- **Processing:** Hugging Face Mistral for NLU
- **Calendar:** Google Calendar API (when authenticated)

### Data Flow
```
User speaks
  ↓
Browser Web Speech API converts to text
  ↓
Frontend fuzzy-matches trigger
  ↓
Frontend sends transcript to /api/voice_cmd
  ↓
Backend parses with Hugging Face
  ↓
Backend returns action + response
  ↓
Frontend speaks response (TTS)
  ↓
Frontend displays events (if applicable)
  ↓
Ready for next trigger
```

---

## Security Best Practices

✅ **Do:**
- Keep `HF_API_KEY` secret (in `.env`, not in code)
- Use HTTPS in production
- Enable login/authentication
- Regularly rotate API keys

❌ **Don't:**
- Share trigger phrase with others
- Store trigger in localStorage (use sessionStorage)
- Commit `.env` to git
- Log transcripts in production

---

## Performance

| Operation | Time |
|-----------|------|
| Speech recognition | <100ms |
| API call | 1-3s |
| TTS speech | <1s |
| **Total** | **2-4s** |

---

## FAQ

**Q: Can I use this offline?**
A: Partially. Speech recognition works offline, but command processing requires HF API. Consider caching responses or using local inference models for full offline mode.

**Q: How many triggers can I have?**
A: Currently one per user. Could be extended to support multiple.

**Q: Will my trigger phrase be visible?**
A: No. It's only stored in sessionStorage and never logged, displayed, or sent to the backend.

**Q: Can I change the voice (male, female, accent)?**
A: Yes! In settings, speech synthesis will show available voices on your system. Note: Voice selection is browser/OS dependent.

**Q: How accurate is the fuzzy matching?**
A: 75%+ similarity on Levenshtein distance. So "Hey Voice" will match "Hey voice", "Hey Voice!", "hei voice" but not "Hey" alone.

**Q: What if I forget my trigger?**
A: You can reset it in settings (requires security check, or you can just set a new one).

**Q: Does it work on mobile?**
A: Partially - Web Speech API support varies by browser. Best on Chrome. Safari has limited support.

---

## Getting Help

1. Check browser console (F12) for errors
2. Check `logs/voice.log` for backend errors
3. Verify `.env` variables are set correctly
4. Test each component independently:
   - Microphone: Try `navigator.mediaDevices.getUserMedia({audio: true})`
   - TTS: Try `speechSynthesis.speak(new SpeechSynthesisUtterance("test"))`
   - API: Try `curl http://localhost:5000/api/voice_cmd` with test data

---

## Next Steps

- [ ] Customize colors in `static/voice-interface.css`
- [ ] Add custom activation sounds in `static/sounds/`
- [ ] Create macros/shortcuts for frequent commands
- [ ] Integrate with smart home devices
- [ ] Deploy to production (use HTTPS!)
- [ ] Create mobile app version

---

**Enjoy your voice assistant!** 🎤

For more details, see:
- `BACKEND_VOICE_IMPLEMENTATION.md` - API details
- `FRONTEND_VOICE_INTERFACE.md` - UI architecture
- `IMPLEMENTATION_SECTIONS_A_AND_B.md` - Complete overview
