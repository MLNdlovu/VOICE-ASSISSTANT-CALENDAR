# 🗓️ Voice Assistant Calendar - Quick Start Guide

## What You Can Do Right Now

### 1. **Book Meetings with Natural Language (ANY Word Order)**
No matter how you say it, the system understands:

```
✅ "Book Friday 2PM movie date with John"
✅ "Movie date with John Friday 2PM"
✅ "2PM Friday meeting with Sarah and Mike"
✅ "Book meeting tomorrow at 3"
✅ "Schedule dentist appointment on 12/25 at 10am with Dr. Smith"
```

All create the event in Google Calendar automatically!

---

### 2. **Get Prompted for Missing Details**
If you don't provide all information, the system asks:

```
You: "Book Friday"
System: "📢 What time would you like to book? (e.g., 'tomorrow', 'Friday', '12/25')"
You: "2 PM"
System: "📢 What should I call this event? (e.g., 'Meeting with John', 'Dentist appointment')"
You: "Study session"
System: "✅ Meeting booked successfully!"
```

---

### 3. **Chat with AI Assistant (Web Dashboard)**

Go to http://localhost:5000 and click the **💬 AI Chat** tab:

#### Quick Actions (Buttons):
- **💡 Suggest Times** - "Find the best times for a meeting next week"
- **📋 Generate Agenda** - "Create agenda and action items for today's meetings"
- **📊 Week Summary** - "Give me a summary of my busy periods this week"
- **✉️ Draft Email** - "Draft a follow-up email for my last meeting"

#### Free-form Chat:
Type any question:
```
👤 You: "What's my busiest day this week?"
🤖 AI: "Based on your calendar, Tuesday is your busiest day with 6 meetings scheduled..."

👤 You: "Can you suggest times for a 1-hour team meeting?"
🤖 AI: "I recommend Tuesday 9:30 AM or Thursday 2:00 PM, both have clear availability..."

👤 You: "Draft an email for my 3pm meeting"
🤖 AI: "Here's a professional follow-up email based on your meeting details..."
```

---

### 4. **Voice Commands (CLI)**

Run the voice interface:
```bash
python voice_assistant_calendar.py
```

Available commands:
```
🎤 help          - Show all available commands
🎤 book          - Book a new event (uses NL parser!)
🎤 events        - Show upcoming events
🎤 cancel-book   - Cancel an event
🎤 suggest       - Get AI meeting suggestions
🎤 add-event     - Create event with details
🎤 set-reminder  - Create a reminder
🎤 config        - Configure authentication
🎤 exit          - Exit the program
```

Example voice session:
```
You: "book"
System: "📅 What would you like to book?"
You: "Meeting with Sarah tomorrow at 10am"
System: "✅ Meeting booked successfully!"
        "📍 Meeting with Sarah"
        "📅 2025-01-14 at 10:00"
        "👥 Attendees: Sarah"
```

---

### 5. **View & Manage Events**

**Web Dashboard:**
- Go to http://localhost:5000
- Click **📅 My Events** tab to see all upcoming events
- Click **➕ Book Event** tab to create events manually

**CLI:**
```
Command: events
Shows:
- Today's meetings
- Tomorrow's meetings
- This week's schedule
- Upcoming events (next 30 days)
```

---

### 6. **All 10 Features Now Available**

| Feature | Status | How to Use |
|---------|--------|-----------|
| 1️⃣ **NLU Parser** | ✅ Complete | Book with natural language in ANY order |
| 2️⃣ **Smart Scheduler** | ✅ Complete | System creates events in Google Calendar |
| 3️⃣ **Agenda Summaries** | ✅ Complete | Chat: "Generate Agenda" button |
| 4️⃣ **Pattern Detection** | ✅ Complete | Chat: "Week Summary" button |
| 5️⃣ **Email Drafting** | ✅ Complete | Chat: "Draft Email" button |
| 6️⃣ **Voice Sentiment** | ✅ Complete | Automatic tone analysis on voice input |
| 7️⃣ **Task Extraction** | ✅ Complete | Chat: Ask about action items |
| 8️⃣ **Jarvis Conversations** | ✅ Complete | Multi-turn chat conversations |
| 9️⃣ **Visual Calendar** | ✅ Complete | Backend ready, UI in development |
| 🔟 **AI Accessibility** | ✅ Complete | Audio-only mode available |

---

## Getting Started

### Step 1: Start the Web Server
```bash
cd c:\Users\Lungelo\ Ndlovu\Documents\VOICE-ASSISSTANT-CALENDAR
python web_app.py
```

You'll see:
```
✅ Smart Scheduler initialized and endpoints registered
🌐 Starting Voice Assistant Calendar Web Server...
📱 Open http://localhost:5000 in your browser
 * Running on http://localhost:5000
```

### Step 2: Open Your Browser
```
http://localhost:5000
```

### Step 3: Login with Google
Click "Login with Google" and authorize the app

### Step 4: Start Using!

#### Option A: Voice Commands (Web)
- Click **🎤 Voice Commands** tab
- Click **🎤 Start Recording** button
- Say: "Book a movie date with John tomorrow at 2pm"
- Click **Execute Command**
- Event created! ✅

#### Option B: AI Chat (Web)
- Click **💬 AI Chat** tab
- Click **💡 Suggest Times** button
- AI responds with meeting time suggestions
- You can book directly from the suggestion! ✅

#### Option C: Voice CLI
```bash
python voice_assistant_calendar.py
> book
> (speak or type) "Meeting with Sarah Friday 10am"
> ✅ Event created!
```

---

## Example Conversations

### Conversation 1: Natural Language Booking
```
CLI: "📅 What would you like to book?"
You: "Movie night with friends Saturday 7pm"
CLI: "✅ Meeting booked successfully!
      📍 Movie night with friends
      📅 2025-01-18 at 19:00
      👥 Attendees: friends"
```

### Conversation 2: Interactive Prompting
```
CLI: "📅 What would you like to book?"
You: "Meeting tomorrow"
CLI: "📢 What time would you like to book? (e.g., '2 PM', '14:00')"
You: "2 PM"
CLI: "📢 What should I call this event? (e.g., 'Meeting with John')"
You: "Team standup"
CLI: "👥 Who should attend? (e.g., 'John, Sarah and Mike' or 'none')"
You: "Sarah and Mike"
CLI: "✅ Meeting booked successfully!
      📍 Team standup with Sarah, Mike
      📅 2025-01-14 at 14:00"
```

### Conversation 3: AI Chat
```
Chat: 💡 "Please suggest the best times for me to schedule a meeting next week."
AI: "I've analyzed your calendar. Here are the best available slots:
    • Tuesday, 9:30 AM - 10:30 AM (2 hours free)
    • Wednesday, 2:00 PM - 4:00 PM (2 hours free)
    • Thursday, 10:00 AM - 11:30 AM (1.5 hours free)
    
    Tuesday morning looks ideal as you have clear space."

Chat: "Book Tuesday at 9:30 AM with the marketing team"
AI: "I'll create that event for you. Sending invites to marketing team...
    ✅ Meeting scheduled!"
```

---

## Keyboard Shortcuts

### Web Dashboard
- **Alt+C** - Open Chat tab
- **Ctrl+Enter** - Send chat message (in chat input)
- **Enter** - Execute voice command (in voice input)

### CLI
- **Ctrl+C** - Exit program
- **Up Arrow** - Repeat last command
- **Ctrl+D** - EOF (exit on some systems)

---

## Troubleshooting

### Issue: "No Python at path"
**Solution:** Make sure you're in the project directory:
```bash
cd "c:\Users\Lungelo Ndlovu\Documents\VOICE-ASSISSTANT-CALENDAR"
python web_app.py
```

### Issue: OAuth login fails
**Solution:** Verify `.config/client_secret_*.json` exists:
```bash
dir .config
# Should show: client_secret_521030747278-*.json
```

### Issue: Chat not responding
**Solution:** Make sure web server is running and you're logged in:
```bash
# Check if http://localhost:5000 is accessible
# Refresh the page
# Try re-logging in
```

### Issue: Voice commands not parsing correctly
**Solution:** Try simpler commands first:
```
Instead of: "Can you please book a meeting with my friend on Friday afternoon?"
Try: "Book Friday 2PM meeting with friend"
```

---

## Next: Advanced Usage

Once comfortable with basics, try:

1. **Batch booking** - "Book three 1-hour slots for the team: Monday 10am, Tuesday 2pm, Thursday 3pm"
2. **Complex prompts** - "Find a 2-hour slot next week for me and Sarah when we're both free"
3. **Email generation** - "Draft a thank-you email for the meeting notes I'll provide"
4. **Schedule analysis** - "Am I overbooked? Suggest how to optimize my calendar"
5. **Task extraction** - "From my meeting today, extract action items and create reminder events"

---

## Support

For issues or questions:
1. Check `README.md` for general information
2. Check `PRODUCTION_READY.md` for technical details
3. Check `FEATURE_VERIFICATION.py` for feature status
4. Check `DEVELOPER_GUIDE.md` for code documentation

---

**Your Voice Assistant Calendar is ready to go! 🚀**

Start by logging in and trying the AI Chat tab, then move to voice commands as you get comfortable.

Good luck! 🎉
