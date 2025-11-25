# AI Smart Scheduler - Quick Reference

## Voice Commands
```
"Find the best time for a 2-hour session sometime next week"
"Find best time for 1-hour meeting next Friday"
"What time should I have a 90-minute team meeting?"
"When can we meet for 2 hours this week?"
"Find availability for a 1-hour session"
```

## How It Works

### 1️⃣ Parse
Your voice input is parsed for:
- **Duration**: "2-hour" → 120 min
- **Window**: "next week" → 7 days  
- **Description**: "team meeting"
- **Constraints**: "Friday morning" → specific day/time

### 2️⃣ Fetch Calendar
Smart Scheduler retrieves your Google Calendar events for the search period.

### 3️⃣ Build Availability
Finds all free time slots that:
- Match required duration
- Respect your preferences (no weekends, etc.)
- Stay within work hours (default: 9-5)

### 4️⃣ Rank with AI
GPT-3.5 evaluates each slot for:
- Time of day suitability
- Buffer time from other events
- Alignment with your stated preferences

### 5️⃣ Recommend
Returns top 3 options with reasoning via:
- **Voice**: "Here are three good times..."
- **Dashboard**: Display with calendar integration
- **API**: JSON with full details

## Configuration (Preferences)

Default behavior:
- ✅ Weekdays only (no weekends)
- ✅ Afternoon preferred (9 AM - 5 PM)
- ✅ Avoid early mornings before 9 AM
- ✅ Minimum 15-minute gap between events

Customize in `src/scheduler_handler.py`:
```python
SchedulePreferences(
    avoid_times=['morning', 'weekend'],
    preferred_times=['afternoon'],
    work_hours_only=True,
    earliest_hour=9,
    latest_hour=17,
    min_gap_minutes=15
)
```

## API Endpoints

### Find Best Times (Structured)
```bash
curl -X POST http://localhost:5000/api/schedule/find-best-times \
  -H "Content-Type: application/json" \
  -d '{
    "event_description": "2-hour meeting",
    "duration_minutes": 120,
    "search_window_days": 7
  }'
```

**Response:**
```json
{
  "event": "2-hour meeting",
  "duration_minutes": 120,
  "total_available_slots": 12,
  "recommendations": [
    {
      "start": "2025-11-27T14:00:00",
      "end": "2025-11-27T16:00:00",
      "reason": "Thursday afternoon, optimal for team availability"
    }
  ]
}
```

### Natural Language Parsing
```bash
curl -X POST http://localhost:5000/api/schedule/parse-and-recommend \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Find the best time for a 2-hour session next week"
  }'
```

## Python Usage

```python
from src.ai_scheduler import SmartScheduler, SchedulePreferences

# Setup
prefs = SchedulePreferences(avoid_times=['morning', 'weekend'])
scheduler = SmartScheduler(
    google_credentials_path='.config/credentials.json',
    preferences=prefs
)

# Find times
results = scheduler.find_best_times(
    event_description="Team standup",
    duration_minutes=30,
    search_window_days=7,
    top_n=3
)

# Use results
for rec in results['recommendations']:
    print(f"Available: {rec['start']}")
```

## NLU Examples

| Input | Parsed As |
|-------|-----------|
| "Find best time for 2-hour session next week" | 120 min, 7 days |
| "1-hour meeting Friday morning nothing too early" | 60 min, Friday 9 AM+ |
| "Plan daily 1-hour revision each day this week" | 60 min, daily through end of week |
| "Remind me day before assignment due" | Relative: -1 day from due date |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No slots found" | Check calendar has free time; reduce duration |
| "Scheduler not initialized" | Verify credentials.json path; enable Calendar API |
| "Error calling GPT" | Set OPENAI_API_KEY env var; check API key valid |
| "Wrong times suggested" | Check preferences; adjust earliest_hour/latest_hour |

## Files

| File | Purpose |
|------|---------|
| `src/ai_scheduler.py` | Core scheduler engine |
| `src/nlu.py` | Natural language parser |
| `src/voice_handler.py` | Voice command patterns |
| `src/scheduler_handler.py` | Web API & integration |
| `tests/test_ai_scheduler.py` | Unit tests |
| `tests/test_nlu.py` | NLU parser tests |
| `SCHEDULER_GUIDE.md` | Detailed documentation |

## Testing

```bash
# Test NLU
pytest tests/test_nlu.py -v

# Test scheduler
pytest tests/test_ai_scheduler.py -v

# Run demo
python demo_scheduler.py
```

## Environment Setup

```bash
# Install dependencies
pip install -r requirements-voice.txt

# Set API key
export OPENAI_API_KEY="sk-..."

# Run app
python web_app.py
```

## Key Features

✅ **Smart Availability Analysis**: Finds truly free time  
✅ **Preference Aware**: Respects user scheduling constraints  
✅ **GPT-Powered**: AI ranks options intelligently  
✅ **Natural Language**: Understands messy voice input  
✅ **Calendar Integration**: Checks Google Calendar  
✅ **Multi-Interface**: Voice, web API, dashboard  
✅ **Fallback Modes**: Works without Calendar or GPT  

---
**Need help?** See `SCHEDULER_GUIDE.md` for full documentation.
