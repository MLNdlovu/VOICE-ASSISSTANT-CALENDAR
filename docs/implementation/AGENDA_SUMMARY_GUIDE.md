# 📅 AI Agenda Summaries - User Guide

## Overview

The Agenda Summary feature generates natural, human-friendly summaries of your calendar for any time period.

Users can say:
```
"What's my day looking like?"
"Summarize my whole week."
"How packed is my schedule?"
"What's coming up today?"
"Brief me on this week"
```

The system responds with natural language summaries like:
```
"You've got a chilled Monday: one study session at 10, then a 3PM meeting. Nothing urgent."
"Your week is packed: 12 meetings scheduled. Wednesday is your busiest day with 4 back-to-back sessions."
"Pretty light schedule today - just one 30-minute call at 2pm."
```

---

## Features

### 1. **Natural Language Summaries**
- Conversational, friendly tone
- Contextual descriptions (light, packed, busy, chilled)
- Event categorization (meeting, class, call, focus time, break)
- Smart time grouping (morning events, afternoon meetings, etc.)

### 2. **Flexible Time Periods**
- Daily summaries ("What's my day looking like?")
- Weekly summaries ("Summarize my week")
- Monthly summaries ("What's my month looking like?")
- Custom ranges

### 3. **Metrics & Details**
- Total events count
- Busy/free time analysis
- Busiest/lightest days
- Event conflict detection
- Calendar density percentage

### 4. **GPT Enhancement** (optional)
- AI personalization for tone
- Actionable insights ("You have ample time for deep work today")
- Tone options: friendly, professional, casual, brief

### 5. **Multi-Interface**
- Voice commands (spoken output)
- Web API (JSON responses)
- Dashboard display (formatted HTML)
- Python library (programmatic access)

---

## Voice Commands

### Day Summaries
```
"What's my day looking like?"
"What do I have today?"
"What's on my agenda?"
"How busy is today?"
"Brief me on today"
```

### Week Summaries
```
"Summarize my week"
"Give me a week summary"
"What's coming up this week?"
"How packed is my week?"
"Brief me on this week"
```

### Month Summaries
```
"Summarize my month"
"Give me a month summary"
"What does my month look like?"
```

### Quick vs. Detailed
```
"Quick summary of my day"      # Fast, no AI enhancement
"Tell me about my week"         # With AI insights
"Brief overview of today"       # Concise format
```

---

## API Endpoints

### Get Agenda Summary
```http
POST /api/schedule/agenda-summary
Content-Type: application/json

{
    "period": "day" | "week" | "month",
    "use_gpt": true | false,
    "calendar_events": [...]  // optional Google Calendar events
}
```

**Response:**
```json
{
    "summary": "You've got a chilled Monday: one study session at 10, then a 3PM meeting. Nothing urgent.",
    "period": "day",
    "event_count": 2,
    "metrics": {
        "total_events": 2,
        "busy_minutes": 120,
        "free_minutes": 1320,
        "first_event_time": "2025-11-25T10:00:00",
        "last_event_time": "2025-11-25T16:00:00",
        "busiest_hour": 15,
        "has_conflicts": false
    }
}
```

### Get Voice Response
```http
POST /api/schedule/agenda-voice
Content-Type: application/json

{
    "result": <summary result from above>
}
```

**Response:**
```json
{
    "voice_response": "You've got a chilled Monday: one study session at 10, then a 3PM meeting. Nothing urgent."
}
```

---

## Python Usage

### Basic Summary
```python
from src.agenda_summary import AgendaSummaryService, AgendaEvent
import datetime

# Create service
service = AgendaSummaryService(use_gpt=False)

# Create mock events
today = datetime.datetime.now()
events = [
    AgendaEvent("Study", today.replace(hour=10), today.replace(hour=11), 60),
    AgendaEvent("Meeting", today.replace(hour=15), today.replace(hour=16), 60),
]

# Get summary
summary = service.get_today_summary(events)
print(summary)
# Output: "You've got a chilled Monday: one study session at 10, then a 3PM meeting. Nothing urgent."
```

### With Metrics
```python
result = service.get_summary_with_details(events, period="day")
print(result['summary'])
print(f"Events: {result['event_count']}")
print(f"Metrics: {result['metrics']}")
```

### Week Summary
```python
week_summary = service.get_week_summary(events)
print(week_summary)
```

### With GPT Enhancement
```python
service = AgendaSummaryService(use_gpt=True)  # Requires OPENAI_API_KEY
summary = service.get_today_summary(events, use_gpt=True)
```

---

## Summary Tones

Automatically selected based on busyness:

| Busy Minutes | Tone | Example |
|-------------|------|---------|
| < 120 min (2 hrs) | Relaxed | "Pretty light schedule today" |
| < 360 min (6 hrs) | Casual | "You've got a chilled Monday" |
| < 540 min (9 hrs) | Neutral | "Moderately busy Monday" |
| > 540 min | Busy | "Packed Monday" |

---

## Event Categories

Automatically detected from event title/description:

| Category | Keywords |
|----------|----------|
| Meeting | meeting, sync, standup, huddle |
| Class | class, lecture, course, training |
| Focus | focus, deep work, development, coding |
| Call | call, zoom, teams, video |
| Break | break, lunch, coffee |
| Social | lunch, dinner, hangout, friend |
| Admin | admin, paperwork, email |

---

## Configuration

### User Preferences (in scheduler_handler.py)
```python
# Time preferences
avoid_times=['morning', 'weekend']
preferred_times=['afternoon']

# Work hours
earliest_hour=9
latest_hour=17

# Tone/style
gpt_tone='friendly'  # or 'professional', 'casual', 'brief'
```

---

## Time Grouping Examples

### Light Day (1-2 hours busy)
```
Input: 1 event at 3 PM
Output: "Pretty light schedule today - just one meeting at 3pm."
```

### Moderate Day (2-6 hours busy)
```
Input: 4 events scattered throughout day
Output: "You've got a chilled Tuesday: one morning session, then afternoon meetings. Plenty of free time."
```

### Packed Day (8+ hours busy)
```
Input: 8 events, back-to-back
Output: "Packed Thursday: 8 events from 9am to 5pm. Back-to-back sessions. No breaks."
```

---

## Week Summary Examples

### Light Week (< 10 events)
```
"Light week ahead: 5 events total. Mostly concentrated Monday and Wednesday."
```

### Moderate Week (10-20 events)
```
"Moderately busy week: 15 meetings scheduled. Spread across all days. Wednesday is your busiest day with 4 events."
```

### Packed Week (20+ events)
```
"Your week is packed: 25 meetings on the calendar. Monday and Thursday are your busiest days with 5 events each."
```

---

## Insights & Actionable Info

With GPT enabled, summaries can include:

### Productivity Insights
```
"You have ample time for deep work today between 11am-2pm."
```

### Wellbeing Tips
```
"Schedule a 20-minute break - you're back-to-back from 9-4."
```

### Collaboration Opportunities
```
"Most of your meetings are one-on-ones; consider some team syncs."
```

### Time Management
```
"You have 3 hours of free time today - perfect for admin tasks."
```

---

## API Examples

### cURL
```bash
# Get day summary
curl -X POST http://localhost:5000/api/schedule/agenda-summary \
  -H "Content-Type: application/json" \
  -d '{"period": "day", "use_gpt": false}'

# Get week summary with GPT
curl -X POST http://localhost:5000/api/schedule/agenda-summary \
  -H "Content-Type: application/json" \
  -d '{"period": "week", "use_gpt": true}'
```

### JavaScript
```javascript
// Get summary
const response = await fetch('/api/schedule/agenda-summary', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        period: 'day',
        use_gpt: true
    })
});

const result = await response.json();
console.log(result.summary);

// Get voice response
const voiceResp = await fetch('/api/schedule/agenda-voice', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({result})
});

const voiceResult = await voiceResp.json();
console.log(voiceResult.voice_response);
```

---

## Metrics Explained

- **total_events**: Number of events in the period
- **busy_minutes**: Total minutes with scheduled events
- **free_minutes**: Total free time
- **first_event_time**: When your first event starts
- **last_event_time**: When your last event ends
- **busiest_hour**: Hour with most events
- **has_conflicts**: Whether overlapping events exist
- **event_types**: Categories of events scheduled

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Summary says "no events" but there are events | Check event times are in correct timezone |
| GPT summary not personalizing | Verify OPENAI_API_KEY is set |
| Times showing in wrong timezone | Ensure calendar events have timezone info |
| Missing event categories | Check event title matches category keywords |

---

## Integration with Other Features

### + Smart Scheduling
Combine with "Find best time" to get:
```
User: "What's my week looking like?"
AI: "Packed week: 15 meetings. Wednesday is busiest."
User: "Find me 2 hours for deep work"
AI: "Best slots: Tuesday morning or Friday afternoon"
```

### + Voice Assistant
```
User: "Brief me on today"
AI: [Speaks summary via TTS]
"You've got a chilled Monday with just two meetings."
```

### + Calendar Dashboard
```
Display:
- Summary at top
- Timeline of events
- Busy/free blocks
- Recommended focus time
```

---

## Performance

- **Calendar fetch**: 1-2 seconds
- **Summary generation**: < 500ms (without GPT)
- **GPT enhancement**: 2-4 seconds
- **Total response time**: 3-6 seconds with GPT

---

## Future Features

- 📊 Weekly trends ("Your Mondays are busier than Fridays")
- 🔄 Recurring event insights
- 🎯 Productivity recommendations
- 📱 Smart notifications ("You have 30 min before next meeting")
- 🌍 Multi-timezone support
- 📈 Historical patterns and predictions
- 👥 Team availability views
