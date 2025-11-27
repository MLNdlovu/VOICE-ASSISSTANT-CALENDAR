# Complete Voice Assistant Integration Test

## Prerequisites
1. Server running: `python web_app.py` (port 5000)
2. Logged in to browser at http://localhost:5000
3. Profile completed with trigger (e.g., `VAC20` or `LN21`)
4. Google Calendar OAuth connected
5. DevTools Console open to watch logs

## Test Flow (5 minutes)

### Step 1: Trigger Recognition
- **Action**: Say your trigger phrase aloud (e.g., "VAC20" or "LN21")
- **Expected**: 
  - Interim text shows: `"vac 20" (waiting for trigger: VAC20)`
  - After ~2s silence: Assistant responds "What can I do for you today?"
  - Listen state continues (blue indicator pulsing)
- **Verify**: 
  - Check console: No repeated "I did not recognize that" messages
  - Chat shows single interim message (not multiple fragments)

### Step 2: Book Meeting Command
- **Action**: Say "Book a meeting tomorrow at 10am"
- **Expected**:
  - Interim text updates to show your speech
  - Auto-submit after 2s silence
  - Response: "I can help you book a meeting. What time would you like?"
  - Follow-up: "What time do you want to book the meeting?"
  - UI ready for next voice input
- **Verify**:
  - No message spam in chat
  - Single response from assistant
  - Listening indicator shows ready for next command

### Step 3: Provide Meeting Details (if multi-turn needed)
- **Action**: Say "Tomorrow at 10 am" (if needed for time clarification)
- **Expected**:
  - System captures details
  - Could trigger save to calendar or ask for confirmation
- **Verify**:
  - Event saved to Google Calendar (check calendar after test)

### Step 4: List Events Command
- **Action**: Say "Show me my events" or "List my events"
- **Expected**:
  - Response: "Retrieving your calendar events"
  - After fetch: "You have [N] upcoming events: [Event1, Event2, ...]"
  - Events displayed in chat
- **Verify**:
  - Events match your Google Calendar
  - No errors in console
  - Chat shows event list clearly

### Step 5: General Question (AI Integration)
- **Action**: Say "What is 2 plus 2?" or "What time is it?"
- **Expected**:
  - Response: Answer to your question
  - Or: "I did not understand that. Please try again."
- **Verify**:
  - Question is captured
  - Response is relevant
  - No hang-ups or timeouts

### Step 6: Stop/Deactivate
- **Action**: Say "Stop listening" or "Goodbye"
- **Expected**:
  - Response: "Voice assistant deactivated."
  - Listening stops
  - Voice indicator goes idle
- **Verify**:
  - No further listening after deactivation
  - Can re-activate by saying trigger again

## Success Criteria
✅ **All of the following must pass:**

1. Trigger phrase recognized without repeated "I did not recognize" loops
2. "What can I do for you today?" appears after trigger
3. Book command recognized and processed
4. List events command fetches and displays events
5. No message spam (interim consolidation working)
6. No console errors
7. Auto-submit works (no need to click button)
8. All responses are spoken aloud by assistant (TTS working)
9. Can book, list, and ask questions in sequence
10. Session ends cleanly without errors

## Troubleshooting

**Issue**: Repeated "I did not recognize" messages
- **Fix**: Browser likely captured assistant's own TTS. Reload page and ensure microphone permissions allow only input, not capture of speaker output.

**Issue**: No interim text showing
- **Fix**: Check browser supports Web Speech API (Chrome recommended). Check DevTools → Console for errors.

**Issue**: Events not showing
- **Fix**: Verify Google Calendar OAuth is connected. Check calendar has events in next 5 days.

**Issue**: Auto-submit not happening after 2s
- **Fix**: Verify `silenceTimeoutMs = 2000` in `voice-assistant.js`. You can increase to 2500 or 3000 if needed.

**Issue**: "What can I do for you today?" not appearing
- **Fix**: Verify trigger was recognized. Check console for `/api/voice/process-command` response with `state: 'trigger_detected'`.

## Quick Terminal Test (Optional)
If web UI doesn't work, test backend directly:

```bash
# 1. Start server
python web_app.py

# 2. In another terminal, test voice/start endpoint:
curl -X POST http://localhost:5000/api/voice/start \
  -H "Content-Type: application/json" \
  -b "access_token=YOUR_TOKEN"

# 3. Test process-command with trigger:
curl -X POST http://localhost:5000/api/voice/process-command \
  -H "Content-Type: application/json" \
  -d '{"text":"VAC20"}' \
  -b "access_token=YOUR_TOKEN"
```

## Notes
- All features are web-first (no desktop app, no Android port planned at this time)
- Voice input/output use browser Web Speech API (free, no external dependencies)
- Google Calendar integration via OAuth (read/write events)
- Session timeout: 7 days
- All transcripts auto-saved to `.config/conversations/`
