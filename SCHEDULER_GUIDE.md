# AI Smart Scheduling Integration Guide

## Overview
The AI Smart Scheduler module enables users to find the best time for events using natural language commands. It:

- Fetches Google Calendar availability
- Respects user preferences (avoid mornings, weekends, etc.)
- Analyzes free slots and busy patterns
- Uses GPT to recommend optimal times
- Integrates with voice commands and dashboard

## Features Implemented

### 1. **AI Scheduler Module** (`src/ai_scheduler.py`)
- `SmartScheduler`: Main orchestrator for finding best times
- `GoogleCalendarHelper`: Fetches events from Google Calendar
- `AvailabilityBuilder`: Builds free time slots from busy events
- `GPTTimeRecommender`: Uses GPT-3.5 to rank and recommend slots
- `SchedulePreferences`: User preference configuration (avoid times, work hours, etc.)
- `TimeSlot`: Data class for available times

### 2. **NLU Parser** (`src/nlu.py`)
Parses messy human language:
```
"Find the best time for a 2-hour session sometime next week."
"Set up something with Vusi Friday morning — nothing too early."
"Plan a 1-hour revision session each day this week."
```

### 3. **Voice Command Integration** (`src/voice_handler.py`)
Added command patterns:
```python
FIND_BEST_TIME_PATTERNS = [
    r"find\s+(?:the\s+)?best\s+time",
    r"find\s+(?:a\s+)?time\s+for",
    r"best\s+time\s+for",
    # ...
]
```

Command parsing extracts:
- Duration (e.g., "2-hour" → 120 minutes)
- Search window (e.g., "next week" → 7 days)
- Event description

### 4. **Web API Endpoints** (`src/scheduler_handler.py`)
Registered in `web_app.py`:

#### Find Best Times (Structured)
```bash
POST /api/schedule/find-best-times
{
    "event_description": "2-hour meeting",
    "duration_minutes": 120,
    "search_window_days": 7
}
```

#### Parse & Recommend (Natural Language)
```bash
POST /api/schedule/parse-and-recommend
{
    "text": "Find the best time for a 2-hour session next week"
}
```

#### Voice Response Generation
```bash
POST /api/schedule/voice-response
{
    "results": <results dict>
}
```

## Usage Examples

### Command Line / Python
```python
from src.ai_scheduler import SmartScheduler, SchedulePreferences

# Create preferences
prefs = SchedulePreferences(
    avoid_times=['morning', 'weekend'],
    preferred_times=['afternoon'],
    work_hours_only=True
)

# Initialize scheduler
scheduler = SmartScheduler(
    google_credentials_path='.config/credentials.json',
    preferences=prefs
)

# Find best times
results = scheduler.find_best_times(
    event_description="2-hour team meeting",
    duration_minutes=120,
    search_window_days=7,
    top_n=3
)

print(results)
```

### Voice Command
```
"Find the best time for a 2-hour session sometime next week."
```

The system will:
1. Parse the command using NLU
2. Extract: duration=120 min, window=7 days, description="session"
3. Fetch Google Calendar events
4. Find available slots matching preferences
5. Use GPT to rank and recommend best times
6. Return top 3 recommendations with reasoning

### Web Dashboard (JavaScript)
```javascript
// Call API for natural language booking
fetch('/api/schedule/parse-and-recommend', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        text: "Find the best time for a 2-hour session next week"
    })
})
.then(r => r.json())
.then(data => {
    // Display recommendations
    data.recommendations.forEach(rec => {
        console.log(`${rec.display}: ${rec.reason}`);
    });
});
```

## Prerequisites

1. **Google Calendar Credentials** (`.config/credentials.json`)
   - OAuth 2.0 Client ID credentials from Google Cloud Console
   - Required scopes: `calendar.readonly`

2. **OpenAI API Key** (for GPT recommendations)
   - Set `OPENAI_API_KEY` environment variable
   - Or pass to `SmartScheduler(openai_api_key='sk-...')`

3. **Python Dependencies**
   ```bash
   pip install -r requirements-voice.txt
   ```
   New packages added:
   - `dateparser>=1.1.4` (NLU date parsing)
   - `parsedatetime>=2.13` (Natural language time parsing)

## Configuration

### User Preferences
Customize in `src/scheduler_handler.py`:
```python
preferences = SchedulePreferences(
    avoid_times=['morning', 'weekend'],  # Times to avoid
    preferred_times=['afternoon'],        # Preferred times
    work_hours_only=True,                # Only suggest work hours
    earliest_hour=9,                     # Earliest hour (9am)
    latest_hour=17                       # Latest hour (5pm)
)
```

### Time Windows
Built-in time periods:
- `morning`: 8-11 AM
- `afternoon`: 1-4 PM  
- `evening`: 5-8 PM

Can be adjusted in `src/ai_scheduler.py`.

## Testing

Run unit tests:
```bash
# Test NLU parser
pytest tests/test_nlu.py -v

# Test scheduler
pytest tests/test_ai_scheduler.py -v

# Run all tests
pytest tests/ -v
```

## Architecture

```
User Input (Voice/Web)
    ↓
VoiceCommandParser (voice_handler.py)
    ↓
NLU Parser (nlu.py) - if natural language
    ↓
SchedulerCommandHandler (scheduler_handler.py)
    ↓
SmartScheduler (ai_scheduler.py)
    ├── GoogleCalendarHelper → Fetch events
    ├── AvailabilityBuilder → Find free slots
    └── GPTTimeRecommender → Rank times
    ↓
Formatted Response (Voice/Dashboard)
```

## Fallback Behavior

If GPT is unavailable:
- Returns first N available slots ranked by time
- Includes basic reasoning (e.g., "Available at 10 AM")

If Google Calendar is unavailable:
- Shows potential time slots (not checked against calendar)
- Useful for preference-based recommendations

## Limitations & Future Enhancements

1. **Current Limitations**:
   - Requires Google Calendar OAuth credentials
   - GPT recommendations limited by token context
   - Doesn't consider travel time between events
   - No multi-person availability checking

2. **Future Features**:
   - Multi-person scheduling (find mutual availability)
   - Travel time considerations
   - Task prioritization (urgent vs. flexible)
   - Meeting room availability integration
   - Timezone support for distributed teams
   - Learning from booking patterns

## Troubleshooting

### "No slots found"
- Check calendar has free time
- Reduce search window or duration
- Adjust time preferences

### "Scheduler not initialized"
- Verify `.config/credentials.json` exists
- Check Google Calendar API is enabled
- Verify OAuth scopes include `calendar.readonly`

### "Error calling GPT"
- Check `OPENAI_API_KEY` environment variable
- Verify OpenAI API key is valid
- Check internet connection

### "Parser can't understand command"
- Use simpler phrasing
- Include duration explicitly ("2-hour")
- Specify search window ("next week")
