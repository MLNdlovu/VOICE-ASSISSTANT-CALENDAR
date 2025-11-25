# 🔮 AI Pattern Detection & Predictions Guide

## Overview

The AI Patterns module automatically detects behavioral patterns in your calendar and predicts what you need before you ask. It analyzes your schedule, finds opportunities for improvement, and suggests actionable changes.

### What It Does

- **Detects Patterns**: Identifies busy times, close events, early meetings, focus gaps, and more
- **Predicts Needs**: Learns from patterns to suggest optimizations
- **Recommends Actions**: Provides specific, actionable recommendations
- **Learns Continuously**: Gets better with more calendar data

---

## 🎯 Use Cases

### 1. "You've been busy every Tuesday morning — want me to block that time for learning?"

The system detects that you have recurring meetings on Tuesday mornings and suggests using that consistent time for focused learning instead.

```
Pattern: Consistent Tuesday Mornings (85% confidence)
Insight: You're busy every Tuesday morning — 3 recurring time slots
Recommendation: Block these consistent busy slots for focused learning sessions
```

### 2. "You tend to forget early events — want earlier reminders?"

The system notices you have multiple early morning events without reminders and suggests proactive early notifications.

```
Pattern: Early Morning Reminders Needed (75% confidence)
Insight: 7 early bookings with 5 lacking reminder settings
Recommendation: Enable 10-minute earlier reminders for all morning events
```

### 3. "You booked events 5 minutes apart — want travel time added?"

The system detects back-to-back meetings and suggests adding realistic travel buffers.

```
Pattern: Travel Time Conflicts (80% confidence)
Insight: 3 events with minimal gaps (< 15 min)
Recommendation: Auto-add 15-30 minute travel buffers between events
```

---

## 🧠 Pattern Types

### 1. **Busy Time Patterns**
Detects consistent time blocks when you're always busy.

```
Detection Criteria:
- Events scheduled at same day/time repeatedly (3+ occurrences)
- Consistent across multiple weeks
- Typically meetings, classes, standups

Example Output:
Name: "Consistent Tuesday Mornings"
Confidence: 85%
Description: "You're busy every Tuesday morning — 3 recurring time slots"
Frequency: Regular
```

**Recommendation**: Block these times for learning or deep work.

### 2. **Travel Time Conflicts**
Identifies events scheduled too close together.

```
Detection Criteria:
- Events with < 15 minute gap (configurable)
- Same or adjacent days
- Sequential meetings

Example Output:
Name: "Travel Time Conflicts"
Confidence: 80%
Description: "You booked 3 events with minimal gaps (< 15 min)"
Frequency: Occasional
```

**Recommendation**: Add 15-30 minute buffers between meetings.

### 3. **Early Morning Reminders**
Finds early events that often lack reminders.

```
Detection Criteria:
- Events starting before 9:00 AM
- Missing reminder settings
- Heuristic: Early events are more likely to be missed

Example Output:
Name: "Early Morning Reminders Needed"
Confidence: 75%
Description: "You tend to forget early events — 7 early bookings with 5 without reminders"
Frequency: Regular
```

**Recommendation**: Enable 10-minute earlier reminders for morning events.

### 4. **Limited Focus Time**
Detects when calendar is too packed.

```
Detection Criteria:
- Less than 20% of week free from meetings
- Heavy meeting load
- Limited time for deep work

Example Output:
Name: "Limited Focus Time"
Confidence: 85%
Description: "Your calendar is packed — only 15% free time for deep work"
Frequency: Frequent
```

**Recommendation**: Block 2-3 hours weekly for focus/learning.

### 5. **Lack of Break Time**
Identifies back-to-back events without breaks.

```
Detection Criteria:
- 3+ consecutive events with < 10 minute gaps
- High burnout risk
- No transition time

Example Output:
Name: "Lack of Break Time"
Confidence: 80%
Description: "You have 4 sequences of back-to-back events with no breaks"
Frequency: Regular
```

**Recommendation**: Schedule 15-30 minute breaks between meetings.

### 6. **Abundant Focus Time**
Positive pattern detecting free time for learning.

```
Detection Criteria:
- More than 50% of week free
- Opportunity for skill development
- Good work-life balance

Example Output:
Name: "Abundant Focus Time"
Confidence: 90%
Description: "You've got plenty of unscheduled time — 65% of your week is free"
Frequency: Regular
```

**Recommendation**: Use your free time for skill development and learning.

---

## 🔔 Prediction Categories

### Learning Blocks
- **What**: Recurring learning/focus time blocks
- **When**: Detected from consistent busy patterns or abundant free time
- **Action**: Block time slots, set learning goals, enable deep work

```json
{
  "category": "learning_blocks",
  "insight": "You're busy every Tuesday morning",
  "recommendation": "Block these consistent busy slots for focused learning",
  "priority": "high",
  "actions": [
    "Identify your most consistently busy time slots",
    "Block these slots for focused learning sessions",
    "Set them as recurring calendar blocks",
    "Add learning goals/topics to each block"
  ]
}
```

### Travel Time
- **What**: Buffers between back-to-back events
- **When**: Events scheduled < 15 minutes apart
- **Action**: Add 15-30 minute travel buffers

```json
{
  "category": "travel_time",
  "insight": "You booked events 5 minutes apart",
  "recommendation": "Auto-add 15-30 minute travel buffers between events",
  "priority": "high",
  "actions": [
    "Review events scheduled 5-15 minutes apart",
    "Add 15-30 minute buffer before each meeting",
    "Mark buffers as 'travel time' or 'transition'",
    "Enable reminders for travel buffers"
  ]
}
```

### Reminder
- **What**: Proactive notifications for early events
- **When**: Early morning events (< 9 AM) without reminders
- **Action**: Enable 10-15 minute early reminders

```json
{
  "category": "reminder",
  "insight": "You tend to forget early events",
  "recommendation": "Enable 10-minute earlier reminders for all morning events",
  "priority": "high",
  "actions": [
    "Find all events starting before 9am",
    "Add 10-15 minute earlier reminders",
    "Set notification type to alert/popup",
    "Test with next early morning event"
  ]
}
```

### Focus Time
- **What**: Dedicated deep work blocks
- **When**: Calendar has < 20% free time or > 50% free time
- **Action**: Block 2-3 hour focus sessions

```json
{
  "category": "focus_time",
  "insight": "Your calendar is packed",
  "recommendation": "Block 2-3 hours weekly for deep work",
  "priority": "medium",
  "actions": [
    "Identify your least busy day/time",
    "Block 2-3 hour focus time slots",
    "Disable notifications during focus blocks",
    "Use for deep work, learning, or projects"
  ]
}
```

### Break
- **What**: Recharge time between meetings
- **When**: Back-to-back meetings detected (3+ sequential with no gaps)
- **Action**: Insert 15-30 min breaks

```json
{
  "category": "break",
  "insight": "You have sequences of back-to-back events",
  "recommendation": "Schedule 15-30 minute breaks between meetings",
  "priority": "high",
  "actions": [
    "List all back-to-back event sequences",
    "Insert 15-30 min breaks between meetings",
    "Use for stretching, coffee, or meditation",
    "Make breaks recurring if pattern repeats"
  ]
}
```

---

## 🎙️ Voice Commands

### Get Pattern Analysis

```
"Analyze my schedule"
"What patterns do you see?"
"Any suggestions for my schedule?"
"Predict what I need"
"Find opportunities in my calendar"
"What should I improve?"
"Smart recommendations"
"Help me optimize my schedule"
```

### Apply Recommendations

```
"Apply my learning blocks"
"Enable early reminders"
"Add focus time"
"Block travel buffers"
"Schedule breaks"
"Apply that suggestion"
"Go ahead with the recommendation"
```

---

## 📡 API Endpoints

### Get Predictions

Analyze calendar and predict user patterns/needs.

```http
POST /api/schedule/predictions
Content-Type: application/json

{
  "calendar_events": [...]  // optional, fetches from Google if omitted
}
```

**Response:**
```json
{
  "status": "success",
  "event_count": 42,
  "patterns": [
    {
      "name": "Consistent Tuesday Mornings",
      "confidence": 85,
      "description": "You're busy every Tuesday morning",
      "frequency": "regular"
    }
  ],
  "predictions": [
    {
      "id": "pred_1",
      "category": "learning_blocks",
      "insight": "You're busy every Tuesday morning",
      "recommendation": "Block these slots for learning",
      "actionable": true,
      "priority": "high",
      "confidence": 85
    }
  ],
  "summary": "Strong pattern detected: You're busy every Tuesday morning | 3 actionable insights available",
  "generated_at": "2024-03-15T10:30:00"
}
```

### Apply Prediction

Apply a specific prediction/recommendation.

```http
POST /api/schedule/apply-prediction
Content-Type: application/json

{
  "prediction_id": "pred_1",
  "calendar_events": [...]
}
```

**Response:**
```json
{
  "status": "success",
  "prediction_id": "pred_1",
  "category": "learning_blocks",
  "insight": "You're busy every Tuesday morning",
  "recommendation": "Block these slots for learning",
  "action_plan": {
    "type": "learning_blocks",
    "steps": [
      "Identify your most consistently busy time slots",
      "Block these slots for focused learning sessions",
      "Set them as recurring calendar blocks",
      "Add learning goals/topics to each block"
    ]
  }
}
```

---

## 🐍 Python Usage

### Basic Analysis

```python
from src.ai_patterns import PatternPredictionService

# Initialize service
service = PatternPredictionService(use_gpt=False, min_gap_minutes=15)

# Analyze calendar
events = [...]  # List of calendar events
analysis = service.analyze_calendar(events)

print(f"Event count: {analysis['event_count']}")
print(f"Patterns found: {len(analysis['patterns'])}")
print(f"Predictions: {len(analysis['predictions'])}")
print(f"Summary: {analysis['summary']}")
```

### Examine Patterns

```python
# Get patterns with confidence scores
for pattern in analysis['patterns']:
    print(f"{pattern['name']}: {pattern['confidence']}%")
    print(f"  {pattern['description']}")
    print(f"  Frequency: {pattern['frequency']}")
```

### Get Predictions

```python
# Get actionable predictions sorted by priority
for pred in analysis['predictions']:
    print(f"[{pred['priority'].upper()}] {pred['category']}")
    print(f"  {pred['insight']}")
    print(f"  → {pred['recommendation']}")
```

### Apply Recommendation

```python
# Apply a specific prediction
if analysis['predictions']:
    first_pred = analysis['predictions'][0]
    
    # Create prediction object
    from src.ai_patterns import Prediction
    
    pred = Prediction(
        prediction_id=first_pred['id'],
        category=first_pred['category'],
        insight=first_pred['insight'],
        recommendation=first_pred['recommendation'],
        actionable=True,
        priority=first_pred['priority'],
        confidence=first_pred['confidence'] / 100.0
    )
    
    # Get action plan
    action_plan = service.apply_prediction(pred, events)
    
    for action in action_plan['actions']:
        print(f"→ {action['type']}: {action['description']}")
```

### Custom Configuration

```python
# Customize analyzer settings
service = PatternPredictionService(
    use_gpt=True,           # Use GPT for enhancement
    min_gap_minutes=20      # Consider <20 min gaps as travel issues
)

# Configure analyzers individually
from src.ai_patterns import BusyTimeAnalyzer, ReminderPatternAnalyzer

busy_analyzer = BusyTimeAnalyzer()
reminder_analyzer = ReminderPatternAnalyzer()

# Analyze with custom settings
busy_blocks, busy_patterns = busy_analyzer.analyze(events)
reminder_stats, reminder_patterns = reminder_analyzer.analyze(events)
```

---

## 📊 Pattern Confidence Scores

Confidence indicates how strong the pattern is:

| Confidence | Meaning | Example |
|-----------|---------|---------|
| 90-100% | Very strong pattern | Confirmed busy block appears 4+ times |
| 75-89% | Strong pattern | Clear pattern but some variation |
| 60-74% | Moderate pattern | Pattern exists but needs confirmation |
| < 60% | Weak pattern | Might be coincidence, low reliability |

---

## 🎯 Priority Levels

| Priority | When | Action |
|----------|------|--------|
| 🔴 **HIGH** | Pattern strongly affects workflow | Apply immediately |
| 🟡 **MEDIUM** | Pattern has moderate impact | Consider applying |
| 🟢 **LOW** | Pattern is nice-to-have | Apply when convenient |

---

## 💡 Use Case Examples

### Example 1: Busy Tuesdays

```
Pattern Detected:
"You're busy every Tuesday morning — 3 recurring time slots"
Confidence: 85%

Prediction:
"Block these consistent busy slots for focused learning sessions"
Category: learning_blocks
Priority: HIGH

Action Plan:
1. Identify: Tuesday 9-12 (Standup, Sync, Dev Meeting)
2. Block: Reserve for "Learning Hour"
3. Recurring: Set as weekly calendar blocks
4. Topics: Add AI/ML, Python, System Design
```

### Example 2: Travel Time Issues

```
Pattern Detected:
"You booked events 5 minutes apart"
Confidence: 80%

Prediction:
"Auto-add 15-30 minute travel buffers between events"
Category: travel_time
Priority: HIGH

Action Plan:
1. Identify: Project Review (2:00 PM) → Client Call (2:35 PM)
2. Add: 15-min buffer (2:30-2:45 PM travel time)
3. Mark: "Transit/Setup" or "Travel"
4. Reminders: 5-min alert for travel block
```

### Example 3: Early Morning Optimization

```
Pattern Detected:
"You tend to forget early events — 7 early bookings, 5 without reminders"
Confidence: 75%

Prediction:
"Enable 10-minute earlier reminders for all morning events"
Category: reminder
Priority: HIGH

Action Plan:
1. Find: All events before 9 AM
2. Add: 10-minute earlier reminders
3. Type: Alert/popup notifications
4. Test: Check next Monday morning
```

### Example 4: Focus Time Creation

```
Pattern Detected:
"Your calendar is packed — only 15% free time"
Confidence: 85%

Prediction:
"Block 2-3 hours weekly for deep work"
Category: focus_time
Priority: MEDIUM

Action Plan:
1. Identify: Friday afternoons (currently light)
2. Block: 2:00-5:00 PM Friday focus block
3. Recurring: Every Friday
4. Settings: Disable notifications, calendar as "busy"
```

---

## 🔧 Configuration

### Analyzer Settings

```python
# Adjust travel time threshold
service = PatternPredictionService(min_gap_minutes=20)  # Default: 15

# Use GPT for personalized recommendations
service = PatternPredictionService(use_gpt=True)

# Requires: OPENAI_API_KEY environment variable
```

### Pattern Customization

Modify detection thresholds in `src/ai_patterns.py`:

```python
# Busy pattern threshold (minimum occurrences)
BUSY_BLOCK_MIN_EVENTS = 3  # Events per time block

# Focus time threshold (% of calendar free)
LIMITED_FOCUS_PCT = 0.20  # Less than 20% = "Limited"
ABUNDANT_FOCUS_PCT = 0.50  # More than 50% = "Abundant"

# Travel time threshold (minimum gap in minutes)
MIN_TRAVEL_GAP = 15  # Events < 15 min apart flagged

# Early morning threshold
EARLY_MORNING_HOUR = 9  # Events before 9 AM
```

---

## 🧪 Testing Patterns

Run comprehensive tests:

```bash
pytest tests/test_ai_patterns.py -v
```

Test coverage:
- ✅ Pattern detection accuracy
- ✅ Prediction generation
- ✅ Confidence scoring
- ✅ Action planning
- ✅ Edge cases (empty calendar, malformed data)

---

## 📚 Integration Examples

### With Scheduler

```python
from src.scheduler_handler import SchedulerCommandHandler

handler = SchedulerCommandHandler()

# Analyze patterns and get predictions
result = handler.handle_predict_patterns({})
print(f"Found {len(result['predictions'])} predictions")

# Apply a recommendation
apply_result = handler.handle_apply_prediction({
    'prediction_id': 'pred_1',
    'calendar_events': events
})
print(f"Action plan: {apply_result['action_plan']['steps']}")
```

### With Voice Commands

```
User: "Analyze my schedule"
→ Voice handler parses as "predict-patterns" command
→ SchedulerCommandHandler.handle_predict_patterns()
→ PatternPredictionService.analyze_calendar()
→ Voice output: "I found 3 patterns in your calendar..."

User: "Apply learning blocks"
→ Voice handler parses as "apply-prediction" command
→ SchedulerCommandHandler.handle_apply_prediction()
→ Action plan returned and spoken to user
```

### With Web Dashboard

```python
# In web app
@app.route('/api/schedule/patterns')
def get_patterns():
    handler = SchedulerCommandHandler()
    result = handler.handle_predict_patterns({})
    return jsonify(result)

@app.route('/api/schedule/apply')
def apply_pattern():
    handler = SchedulerCommandHandler()
    result = handler.handle_apply_prediction(request.json)
    return jsonify(result)
```

---

## 🚀 Performance

- **Analysis Time**: 100-500ms for 100 events
- **Pattern Detection**: O(n) where n = number of events
- **Prediction Generation**: O(p) where p = number of patterns
- **GPT Enhancement**: 2-4 seconds additional (if enabled)

---

## 🔐 Privacy & Data

- ✅ All analysis runs locally (no external calls except optional GPT)
- ✅ No data stored persistently
- ✅ Calendar data never leaves your device (without explicit export)
- ✅ Optional GPT enhancement requires OpenAI API key

---

## 🎓 Advanced Features

### Custom Pattern Analyzers

```python
from src.ai_patterns import BusyTimeAnalyzer

class CustomAnalyzer(BusyTimeAnalyzer):
    def analyze(self, events):
        # Custom logic here
        busy_blocks, patterns = super().analyze(events)
        # Post-process if needed
        return busy_blocks, patterns
```

### Pattern Filtering

```python
# Get only high-confidence patterns
high_confidence = [p for p in analysis['patterns'] if p['confidence'] > 0.80]

# Get only high-priority predictions
high_priority = [p for p in analysis['predictions'] if p['priority'] == 'high']
```

### Multi-Week Analysis

```python
# Analyze 8-week trend
from datetime import timedelta

all_events = []
for week in range(8):
    week_events = get_events(
        start=now + timedelta(weeks=week),
        end=now + timedelta(weeks=week+1)
    )
    all_events.extend(week_events)

analysis = service.analyze_calendar(all_events)
```

---

## ❓ FAQ

**Q: How often should I run pattern analysis?**
A: Weekly is ideal. Run after scheduling major changes or monthly to catch long-term trends.

**Q: Can I manually override suggestions?**
A: Yes! Predictions are suggestions. Review and customize before applying.

**Q: Does it learn from my choices?**
A: Current version detects static patterns. Future versions will learn from your acceptance/rejection of suggestions.

**Q: What if confidence is low?**
A: Low-confidence patterns may be noise. Ignore them or investigate manually.

**Q: Can I combine multiple predictions?**
A: Absolutely! Apply travel time buffers + learning blocks + early reminders together.

---

## 📞 Support

- 📖 See `AI_PATTERNS_GUIDE.md` for detailed documentation
- 💬 Voice command examples above
- 🧪 Run `pytest tests/test_ai_patterns.py` for tests
- 🐍 Check `src/ai_patterns.py` for code documentation

---

## 🎉 Next Steps

1. **Run Demo**: `python demo_scheduler.py`
2. **Try Voice**: "Analyze my schedule"
3. **Review Predictions**: Check recommendations dashboard
4. **Apply Changes**: Implement suggested improvements
5. **Monitor Impact**: See if changes improve your productivity

**Ready to let AI optimize your calendar!** 🚀
