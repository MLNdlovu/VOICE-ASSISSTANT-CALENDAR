# 🎙️ Quick Start: GPT-5 Voice Assistant

## ✅ Status: LIVE & READY

Your Voice Assistant Calendar is now live at: **http://localhost:5000**

## 🚀 Getting Started in 2 Minutes

### 1. Open Dashboard
```
http://localhost:5000
```

### 2. Find Voice Trigger Widget
Look for the "Voice Trigger" box at the **bottom-left** of the screen (fixed position)

### 3. Set Your Trigger Phrase
- Type: `hey nova` (or any phrase you like)
- Click: `Save Trigger (Hidden)`
- Your phrase is now stored securely on the server
- It will **never** appear in console or network logs

### 4. Test Voice Commands
Say your trigger phrase followed by a command:

**Examples that work:**
- "Hey nova, book a meeting tomorrow at 2 PM called team standup"
- "Hey nova, show me my events for today"
- "Hey nova, how's my calendar looking for next week?"
- "Hey nova, schedule a review meeting in 1 hour"

### 5. Listen for Response
Assistant will:
1. Say "What can I do for you today?"
2. Listen for your command (8 seconds)
3. Process with OpenAI GPT
4. Speak back the response

## ⚙️ Before You Start: Set OpenAI Key

### Option A: Add API Key to .env (Recommended)
1. Get key: https://platform.openai.com/api-keys
2. Edit `.env` file in project folder:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```
3. Save and restart Flask server
4. Try voice commands again

### Option B: Use Free Alternative (Limited)
- Without key: Assistant will use basic responses
- Some features may be limited
- Not recommended for production

## 📋 What You Can Do

### ✅ Calendar Actions
- **Book**: "Book a meeting tomorrow at 3 PM called sprint planning"
- **List events**: "Show me my events for today"
- **Check availability**: "When's my next meeting?"

### ✅ Natural Language
- "What should I do with my free time?"
- "How many meetings today?"
- "Am I available at 2 PM?"

### ✅ Voice Features
- **Hidden trigger**: Trigger phrase never displayed
- **Auto-disappear**: Message bubbles auto-hide after 3.5s
- **Natural speech**: Times spoken naturally ("2 PM" not "2 . 0 . 0")
- **Stop button**: Click ⏹️ to stop speech immediately

## 🔧 Browser Requirements

✅ **Recommended**: Chrome, Edge, Brave
⚠️ **Limited**: Safari (Web Speech API support limited)
❌ **Not supported**: Firefox (no Web Speech API)

### Enable Microphone Permission
When first using voice, browser will ask:
- **Click "Allow"** to use microphone
- Without this, voice won't work

## 🐛 Troubleshooting

### No voice response?
1. Check browser console (F12 → Console)
2. Look for errors or warnings
3. Verify OpenAI key is set in `.env`
4. Restart Flask server

### Speech recognition not working?
1. Use Chrome/Edge browser
2. Check microphone permission granted
3. Speak clearly and wait for "What can I do?" prompt

### Assistant says strange things?
1. Speak more clearly
2. Add more context to your command
3. Try simpler phrases

### Nothing happens after trigger?
1. Say trigger phrase louder/clearer
2. Wait for "What can I do for you today?" response
3. Check Flask console for errors

## 🎯 Pro Tips

### Tip 1: Better Booking Commands
Instead of: "Book a meeting"
Try: "Book a meeting called standup with john tomorrow at 2 PM"

### Tip 2: Specific Date Commands
Instead of: "Show events"
Try: "Show events for December 20th" or "Show events today"

### Tip 3: Natural Language
The assistant understands:
- "Tomorrow" and "next Monday"
- Time formats: "2 PM", "14:00", "2 o'clock"
- "next week", "in 2 hours"

### Tip 4: Stop Unwanted Speech
If assistant is talking and you want to stop:
- Click **⏹️ Stop** button
- Or say your trigger phrase again to restart

## 📊 What's Running

- **Backend**: Flask on http://localhost:5000
- **Model**: OpenAI gpt-4o-mini
- **API**: RESTful endpoints for voice commands
- **Frontend**: React-based dashboard with voice UI
- **Storage**: In-memory for demo (ready for database)

## 🔐 Security Notes

- Trigger phrase stored server-side only
- Never transmitted in plain text
- OpenAI API key in `.env` (not version controlled)
- Session-based user isolation
- Rate limited to 60 requests/minute

## 📈 Next Steps

After testing basic features:
1. **Integrate Google Calendar** - Use real calendar instead of demo
2. **Add error scenarios** - Test network failures, timeouts
3. **Customize responses** - Adjust how assistant replies
4. **Add more triggers** - Multiple voice commands per trigger

---

**Ready to test?** Open http://localhost:5000 and start talking! 🎙️
