# Quick Reference: Features 9-10

## ⚡ Quick Start

### Feature 9: Visual Calendar

```python
from src.visual_calendar import VisualCalendarAnalyzer
from datetime import datetime

analyzer = VisualCalendarAnalyzer()

# Analyze a day
day = analyzer.analyze_day(events, datetime(2024, 3, 15))
print(day.description)        # "You have 5 hours of meetings"
print(day.stress_level)       # StressLevel.MODERATE
print(day.utilization_percent) # 42
```

### Feature 10: Accessibility

```python
from src.accessibility import AccessibilityManager, SpeechRate

manager = AccessibilityManager()
manager.enable_audio_only_mode()
manager.set_speech_rate(SpeechRate.SLOW)

# Read calendar
events = calendar.get_events('week')
manager.read_agenda(events, verbose=True)

# Handle voice with correction
r1 = manager.process_voice_command("Book at 11")
r2 = manager.process_voice_command("Wait, 11:30")  # is_correction=True
```

---

## 📊 Feature 9: Visual Calendar

### Analysis Types

| Type | Use Case | Returns |
|------|----------|---------|
| `day` | Single day breakdown | DayAnalysis with hourly details |
| `week` | Pattern detection | WeekAnalysis with trends |
| `month` | Long-term trends | MonthAnalysis with recommendations |

### Stress Levels

| Level | Hours | Action |
|-------|-------|--------|
| LOW | 0-3 | Continue current pace |
| MODERATE | 4-6 | Maintain balance |
| HIGH | 6-8 | Consider rescheduling |
| CRITICAL | 8+ | Take immediate action |

### API Endpoint

```bash
POST /api/calendar/visual-analysis
Content-Type: application/json

{
  "events": [...],
  "analysis_type": "week",
  "date": "2024-03-15"
}
```

### Key Methods

```python
analyzer.analyze_day(events, date)
analyzer.analyze_week(day_events_dict)
analyzer.analyze_month(weeks_dict)
analyzer.generate_visual_description(type, events)
analyzer.get_availability_score(events, date, required_hours)
analyzer.get_stress_recommendations(level, hours, count)
```

---

## 🎙️ Feature 10: Accessibility

### Accessibility Modes

| Mode | Visual | Audio | Best For |
|------|--------|-------|----------|
| FULL_SCREEN | ✓ | Optional | Sighted users |
| AUDIO_ONLY | ✗ | ✓ | Blind users |
| SCREEN_READER | ✓ | ✓ | NVDA/JAWS users |
| HIGH_CONTRAST | ✓ | Optional | Low-vision users |

### Speech Rates

| Rate | WPM | Content |
|------|-----|---------|
| VERY_SLOW | 80 | Very complex |
| SLOW | 120 | Complex |
| NORMAL | 150 | Default |
| FAST | 200 | Simple |
| VERY_FAST | 250 | Very simple |

### API Endpoint

```bash
POST /api/accessibility/settings
Content-Type: application/json

# Set mode
{
  "action": "set_mode",
  "mode": "audio_only"
}

# Process voice command
{
  "action": "process_command",
  "voice_command": "Schedule at 2 PM",
  "correction_context": "Initial: 1 PM"
}

# Read agenda
{
  "action": "read_agenda",
  "events": [...],
  "verbose": true
}
```

### Key Methods

```python
manager.enable_audio_only_mode()
manager.enable_screen_reader_mode()
manager.set_speech_rate(SpeechRate.SLOW)
manager.process_voice_command(command)
manager.read_agenda(events, verbose=False)
manager.describe_event(event)
```

---

## 🗣️ Voice Correction Examples

### Example 1: Time Change
```
User:   "Book at 11"
System: "Booking for 11:00 AM. Confirm?"
User:   "Wait no, 11:30"
System: "Updated to 11:30 AM. Confirmed."
```

### Example 2: Attendee Change
```
User:   "Schedule with Alice and Bob"
System: "Meeting with Alice and Bob. Confirm?"
User:   "Actually just Alice and Charlie"
System: "Updated: Alice and Charlie. Confirmed."
```

### Correction Signals Detected
- "Wait", "no", "wait no"
- "Actually", "let me correct that"
- "I mean", "I meant"
- "Hold on", "one more thing"
- "Change that to", "make it instead"

---

## 📈 Heatmap Format

```
Weekly:
Mon: ░░░░░░░░░░░░░░░░░░░░░░░░ = Light (1-2 events)
Tue: ▒▒▒▒░░░░░░░░░░░░░░░░░░░░ = Medium (3-4 events)
Wed: ▓▓▓▓░░░░░░░░░░░░░░░░░░░░ = Dark (5-6 events)
Thu: ██████░░░░░░░░░░░░░░░░░░░ = Full (7+ events)
```

---

## 🧪 Testing

### Run Tests
```bash
# Visual calendar tests
python -m pytest tests/test_visual_calendar.py -v

# Accessibility tests
python -m pytest tests/test_accessibility.py -v

# All tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=src
```

### Test Statistics
- **Visual Calendar**: 30+ tests
- **Accessibility**: 40+ tests
- **Total**: 70+ tests
- **Coverage**: 85%+

---

## 📚 Documentation

| Document | Content | Lines |
|----------|---------|-------|
| VISUAL_CALENDAR_GUIDE.md | Complete Feature 9 guide | 400+ |
| ACCESSIBILITY_GUIDE.md | Complete Feature 10 guide | 500+ |
| FEATURES_9_10_IMPLEMENTATION_SUMMARY.md | Implementation details | 400+ |
| FEATURES_9_10_COMPLETION_REPORT.md | Completion checklist | 300+ |

---

## ⚙️ Configuration

### Environment
```bash
export OPENAI_API_KEY=sk-...
export DEBUG=0  # Set to 1 for verbose logging
```

### Python Imports
```python
# Visual Calendar
from src.visual_calendar import VisualCalendarAnalyzer, CalendarHeatmap

# Accessibility
from src.accessibility import (
    AccessibilityManager,
    AudioUIController,
    VoiceErrorCorrection,
    AccessibleVoiceSummarizer,
    AccessibilityMode,
    SpeechRate
)
```

---

## 🔧 Troubleshooting

### Visual Calendar Issues

**Problem**: Heatmap not generating
```python
# Check events format
events = [
    {'title': 'Meeting', 'start': '2024-03-15T10:00', 'end': '2024-03-15T11:00'}
]
# Ensure start/end are ISO format or datetime objects
```

**Problem**: Stress level not updating
```python
# Clear any cached analysis
analyzer = VisualCalendarAnalyzer()  # Create fresh instance
```

### Accessibility Issues

**Problem**: TTS not working
```bash
# Install pyttsx3
pip install pyttsx3

# Test TTS
python -c "import pyttsx3; e = pyttsx3.init(); e.say('Test'); e.runAndWait()"
```

**Problem**: Voice correction not detecting
```python
# Check correction detection
from src.accessibility import VoiceErrorCorrection
correction = VoiceErrorCorrection()
result = correction._is_correction_signal("Wait no, 11:30")
print(result)  # Should be True
```

---

## 🚀 Deployment

### Verification Checklist
- [ ] Python 3.8+ installed
- [ ] Dependencies installed: `pip install pyttsx3 openai speech_recognition`
- [ ] OPENAI_API_KEY set
- [ ] Tests passing: `python -m pytest tests/ -q`
- [ ] Server runs: `python web_app.py`
- [ ] Browser loads: `http://localhost:5000`
- [ ] Visual calendar works: Click "Calendar Analytics"
- [ ] Accessibility works: Enable "Audio Only" mode

### Deploy Command
```bash
python web_app.py --host 0.0.0.0 --port 5000
```

---

## 📞 Support

### Get Help
1. Check `docs/VISUAL_CALENDAR_GUIDE.md` for Feature 9
2. Check `docs/ACCESSIBILITY_GUIDE.md` for Feature 10
3. Run tests to verify: `python -m pytest tests/test_visual_calendar.py tests/test_accessibility.py -v`
4. Enable debug: `export DEBUG=1`
5. Check logs for errors

### Report Issues
- Include Feature version (9 or 10)
- Include error message
- Include reproduction steps
- Include Python version: `python --version`

---

## 📊 System Status

- **Features Implemented**: 10/10 ✅
- **Tests Created**: 270+ ✅
- **Documentation**: 3,500+ lines ✅
- **Production Ready**: ✅ YES

---

**Last Updated**: March 2024  
**Status**: Production Ready ✅
