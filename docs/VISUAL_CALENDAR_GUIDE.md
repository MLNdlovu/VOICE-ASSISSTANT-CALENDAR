<!-- Visual Calendar Guide -->

# Feature 9: AI-Powered Visual Calendar

## Overview

The Visual Calendar feature enables users to understand their schedule through intelligent visual analytics, heatmaps, and stress level assessment. Perfect for answering questions like:
- "What's my busiest day this week?"
- "When am I most stressed?"
- "Show me a heatmap of my calendar"
- "What days do I have free time?"

## Key Capabilities

### 1. Calendar Heatmaps
- **Weekly Heatmaps**: ASCII-based visualization showing intensity across 7 days
- **Monthly Heatmaps**: Full month overview with stress indicators
- **Unicode Intensity Levels**: Visual representation using ░ (light) to █ (packed)

```
Weekly Heatmap Example:
Mon: ▓░░░░░░░░░░░░░░░░░░░░░░ (Light)
Tue: ████████░░░░░░░░░░░░░░░░ (Busy)
Wed: ██████████████░░░░░░░░░░ (Packed)
```

### 2. Stress Level Analysis
- **LOW**: Free time available, comfortable schedule
- **MODERATE**: Reasonable workload, manageable
- **HIGH**: Packed schedule, limited breaks
- **CRITICAL**: Overwhelming load, immediate action recommended

### 3. Time Slot Intensity
- **FREE**: No events (0 hours)
- **LIGHT**: 1-4 hours of meetings
- **MODERATE**: 4-6 hours of meetings
- **BUSY**: 6-8 hours of meetings
- **PACKED**: 8+ hours of meetings

### 4. Availability Analysis
- Find largest free time blocks
- Identify best times to schedule
- Calculate availability score (0-100%)
- Recommend optimal meeting times

## API Usage

### Visual Calendar Analysis Endpoint

**Endpoint**: `POST /api/calendar/visual-analysis`

**Request**:
```json
{
  "events": [
    {
      "title": "Team Meeting",
      "start": "2024-03-15T10:00:00",
      "end": "2024-03-15T11:00:00",
      "description": "Weekly sync"
    }
  ],
  "analysis_type": "day",
  "date": "2024-03-15"
}
```

**Parameters**:
- `events`: Array of calendar events
- `analysis_type`: "day", "week", or "month"
- `date`: Target date for analysis (ISO format)

**Response**:
```json
{
  "description": "Your Monday is moderately busy with 5 hours of meetings",
  "stress_level": "MODERATE",
  "utilization": 42,
  "event_count": 5,
  "recommendations": [
    "Consider scheduling deep work between 2-3 PM",
    "You have 3 hours of free time available"
  ],
  "heatmap": "Mon: ▓░░░░░░░░░░░░░░░░░░░░░░"
}
```

## Python API

### Basic Usage

```python
from src.visual_calendar import VisualCalendarAnalyzer
from datetime import datetime

# Initialize analyzer
analyzer = VisualCalendarAnalyzer()

# Analyze a single day
events = [
    {'title': 'Meeting', 'start': datetime(2024, 3, 15, 10, 0), 
     'end': datetime(2024, 3, 15, 11, 0)}
]

day_analysis = analyzer.analyze_day(events, datetime(2024, 3, 15))
print(day_analysis.description)
print(f"Stress Level: {day_analysis.stress_level}")
print(f"Utilization: {day_analysis.utilization}%")
```

### Analysis Methods

#### Analyze Single Day
```python
day_analysis = analyzer.analyze_day(
    events=events,
    date=datetime(2024, 3, 15)
)

# Access results
print(day_analysis.intensity)  # TimeSlotIntensity enum
print(day_analysis.stress_level)  # StressLevel enum
print(day_analysis.total_hours)  # Float hours
print(day_analysis.recommendation)  # String
```

#### Analyze Week
```python
week_data = {
    datetime(2024, 3, 15): events,
    datetime(2024, 3, 16): other_events,
    # ... more days
}

week_analysis = analyzer.analyze_week(week_data)

print(week_analysis.busiest_day)  # datetime
print(week_analysis.average_hours)  # Float
print(week_analysis.stress_pattern)  # String
```

#### Analyze Month
```python
month_data = {
    datetime(2024, 3, 1): events,
    datetime(2024, 3, 2): events,
    # ... all days in month
}

month_analysis = analyzer.analyze_month(month_data)

print(month_analysis.overall_stress)  # StressLevel
print(month_analysis.busiest_week)  # Week number
print(month_analysis.trend)  # String trend description
```

### Advanced Features

#### Generate Visual Description
```python
description = analyzer.generate_visual_description(
    analysis_type='week',
    events=week_events,
    use_gpt=True,
    gpt_fallback=True
)
print(description)
```

#### Get Availability Score
```python
availability = analyzer.get_availability_score(
    events=events,
    date=datetime(2024, 3, 15),
    required_hours=2
)
print(f"Availability: {availability}%")
```

#### Get Stress Recommendations
```python
recommendations = analyzer.get_stress_recommendations(
    stress_level=StressLevel.HIGH,
    available_hours=2,
    event_count=8
)

for rec in recommendations:
    print(f"- {rec}")
```

## Data Models

### TimeSlotAnalysis
```python
@dataclass
class TimeSlotAnalysis:
    hour: int
    has_event: bool
    event_title: Optional[str]
    event_duration: float
    is_peak_time: bool
    intensity: TimeSlotIntensity
```

### DayAnalysis
```python
@dataclass
class DayAnalysis:
    date: datetime
    intensity: TimeSlotIntensity
    stress_level: StressLevel
    total_hours: float
    event_count: int
    utilization_percent: int
    busiest_hour: int
    free_slots: List[Tuple[int, int]]
    recommendation: str
    description: str
```

### WeekAnalysis
```python
@dataclass
class WeekAnalysis:
    week_number: int
    average_hours: float
    busiest_day: datetime
    average_stress: StressLevel
    total_events: int
    free_days: int
    stress_pattern: str
    description: str
```

### MonthAnalysis
```python
@dataclass
class MonthAnalysis:
    month: str
    overall_stress: StressLevel
    average_hours_per_day: float
    busiest_week: int
    total_events: int
    trend: str
    recommendation: str
```

## Integration with Scheduler

The Visual Calendar is automatically initialized in `SchedulerHandler`:

```python
from src.scheduler_handler import SchedulerHandler

handler = SchedulerHandler()

# Visual calendar analysis request
result = handler.handle_visual_calendar_analysis({
    'events': calendar_events,
    'analysis_type': 'week',
    'date': datetime.now()
})

print(result['description'])
print(f"Stress: {result['stress_level']}")
```

## Voice Commands

### Example Commands

```
"Analyze my calendar"
→ Returns day/week analysis with descriptions

"What's my busiest day this week?"
→ Identifies busiest day and provides details

"Show me a heatmap"
→ Generates ASCII heatmap visualization

"When am I most stressed?"
→ Analyzes stress patterns and identifies peaks

"How busy am I on Friday?"
→ Provides Friday-specific analysis

"What's my availability next week?"
→ Calculates free time and availability score

"Am I overbooked?"
→ Stress assessment with recommendations
```

## Stress Level Guidelines

### LOW Stress
- **Hours of meetings**: 0-3 per day
- **Action**: Continue current pace
- **Recommendation**: Use extra time for deep work or learning

### MODERATE Stress
- **Hours of meetings**: 4-6 per day
- **Action**: Maintain balance
- **Recommendation**: Schedule breaks between meetings

### HIGH Stress
- **Hours of meetings**: 6-8 per day
- **Action**: Consider rescheduling
- **Recommendation**: Reduce meetings or delegate tasks

### CRITICAL Stress
- **Hours of meetings**: 8+ per day
- **Action**: Take immediate action
- **Recommendation**: Move meetings to next week, reduce commitments

## Heatmap Interpretation

The heatmap uses Unicode intensity characters:
- **░** (Light shade): 1-2 events
- **▒** (Medium shade): 2-4 events
- **▓** (Dark shade): 4-6 events
- **█** (Full block): 6+ events

Example interpretation:
```
Monday:    ░░░░░░░░░░░░░░░░░░░░░░░░ = Light day
Tuesday:   ████░░░░░░░░░░░░░░░░░░░░ = Busy morning
Wednesday: ████████████░░░░░░░░░░░░░ = Heavy schedule
```

## Performance Considerations

- **Analysis Speed**: < 500ms for typical calendars
- **Heatmap Generation**: < 200ms for monthly heatmaps
- **GPT Calls**: Optional, fallback to rules-based descriptions
- **Memory**: Scales linearly with event count

## Error Handling

```python
from src.visual_calendar import VisualCalendarAnalyzer

analyzer = VisualCalendarAnalyzer()

try:
    analysis = analyzer.analyze_day(events, date)
except ValueError as e:
    print(f"Invalid input: {e}")
except Exception as e:
    print(f"Analysis failed, using fallback rules: {e}")
```

## Best Practices

1. **Use appropriate analysis types**
   - Single day for detailed view
   - Week for pattern recognition
   - Month for trend analysis

2. **Combine with other features**
   - Use stress level to prioritize tasks
   - Reference availability scores for scheduling
   - Review recommendations before booking

3. **Monitor trends**
   - Weekly analysis to catch stress buildup
   - Monthly trends for career planning
   - Adjust workload based on patterns

4. **Leverage accessibility**
   - Use with audio summaries for accessibility
   - Enable high-contrast heatmaps for low-vision users
   - Combine with voice commands for hands-free analysis

## Testing

Run the visual calendar tests:

```bash
python -m pytest tests/test_visual_calendar.py -v
```

Tests cover:
- Time slot intensity analysis
- Day/week/month analysis
- Heatmap generation
- Stress level detection
- Availability calculations
- Visual descriptions
- Recommendation generation

## Limitations & Future Enhancements

### Current Limitations
- Heatmaps show event count, not duration
- Stress calculation based on hours only
- No multi-calendar support yet

### Planned Enhancements
- Duration-weighted heatmaps
- Calendar collaboration view
- AI-powered meeting optimization
- Integration with email for forecast
- Time zone support for global teams

## FAQ

**Q: Can I customize stress level thresholds?**
A: Currently using fixed thresholds. Future version will support customization.

**Q: Does this work with recurring events?**
A: Yes, all event types are supported. Provide fully expanded event list.

**Q: What if I have no calendar events?**
A: Analysis returns zero utilization, LOW stress, and recommendations for better planning.

**Q: Can I export the heatmap?**
A: Currently ASCII format. Export to image planned for future release.

## Related Features

- **Feature 1**: NLU Parser (processes calendar queries)
- **Feature 2**: Smart Scheduler (uses availability from visual analysis)
- **Feature 8**: Jarvis Conversations (natural calendar discussions)
- **Feature 10**: Accessibility (audio descriptions of heatmaps)

---

**Version**: 1.0  
**Last Updated**: March 2024  
**Status**: Production Ready
