Voice Sentiment & Emotion Analysis Module
===========================================

Complete Guide to Emotion Detection & Mood-Based Calendar Adjustments

## Overview

The Voice Sentiment module (`src/voice_sentiment.py`) detects emotions and stress levels from voice input, providing mood-aware recommendations and calendar adjustments. It enables truly intelligent scheduling by understanding not just *what* users say, but *how* they feel.

**Key Features:**
- 10 emotion types (HAPPY, STRESSED, ANXIOUS, TIRED, CALM, etc.)
- 4 stress levels (LOW, MODERATE, HIGH, CRITICAL)
- 5 mood states (VERY_POSITIVE → VERY_NEGATIVE)
- Energy level estimation (0-1 scale)
- HuggingFace transformer integration with fallback detection
- Emotion-aware recommendations with confidence scoring
- Mood-based calendar adjustments
- Keyword-based + ML-based detection

---

## Architecture

### Data Structures

```python
# Enums
EmotionType enum:
  - HAPPY: Joyful, content, positive
  - STRESSED: Overwhelmed, tense, pressured
  - ANXIOUS: Worried, nervous, fearful
  - SAD: Depressed, down, unhappy
  - FRUSTRATED: Annoyed, irritated, angry
  - CALM: Relaxed, peaceful, composed
  - NEUTRAL: No particular emotion
  - EXCITED: Energized, enthusiastic
  - TIRED: Exhausted, fatigued, drained
  - CONFUSED: Uncertain, disoriented

StressLevel enum:
  - LOW: Minimal stress, relaxed
  - MODERATE: Normal stress levels
  - HIGH: Elevated stress, concerning
  - CRITICAL: Severe stress, requires intervention

Mood enum:
  - VERY_POSITIVE: Excellent mood
  - POSITIVE: Good mood
  - NEUTRAL: Neither positive nor negative
  - NEGATIVE: Poor mood
  - VERY_NEGATIVE: Severely negative mood

# Data classes
EmotionDetection:
  - primary_emotion: EmotionType - Main detected emotion
  - secondary_emotions: List[Tuple[EmotionType, float]] - Other emotions
  - confidence: float - Detection confidence (0-1)
  - stress_level: StressLevel - Calculated stress level
  - mood: Mood - Overall mood assessment
  - energy_level: float - Energy estimate (0-1)
  - detected_at: datetime - When detection occurred

EmotionResponse:
  - category: str - Type of recommendation
  - action: str - Specific action recommended
  - description: str - Detailed description
  - priority: str - high/medium/low
  - confidence: float - Confidence in recommendation
  - rationale: str - Why this recommendation
```

### Core Classes

#### VoiceSentimentAnalyzer

Main sentiment analysis engine.

```python
class VoiceSentimentAnalyzer:
    def __init__(self, use_transformers: bool = True)
    
    def detect_emotion(text: str, confidence_threshold: float = 0.5) 
        → EmotionDetection
    
    def get_emotion_summary(detection: EmotionDetection) → str
    
    # Internal methods
    def _keyword_based_emotion(text: str) → Tuple[EmotionType, List, float]
    def _calculate_stress_level(text: str, emotion: EmotionType) → StressLevel
    def _calculate_mood(emotion: EmotionType, stress: StressLevel) → Mood
    def _estimate_energy(emotion: EmotionType, stress: StressLevel) → float
```

**Example Usage:**

```python
from src.voice_sentiment import VoiceSentimentAnalyzer

analyzer = VoiceSentimentAnalyzer(use_transformers=True)

# Analyze voice text
text = "Yoh I'm completely stressed and overwhelmed with meetings!"
detection = analyzer.detect_emotion(text)

print(f"Emotion: {detection.primary_emotion.value}")  # "stressed"
print(f"Stress: {detection.stress_level.value}")      # "critical"
print(f"Mood: {detection.mood.value}")                # "very_negative"
print(f"Energy: {detection.energy_level}")            # 0.3

summary = analyzer.get_emotion_summary(detection)
# Output: "I detect you're feeling stressed. Stress level: critical. Energy: 30%"
```

#### EmotionResponseEngine

Generates recommendations based on detected emotions.

```python
class EmotionResponseEngine:
    def get_responses(detection: EmotionDetection) → List[EmotionResponse]
    
    def apply_stress_relief(events: List[Dict], detection: EmotionDetection) 
        → Dict[str, Any]
    
    # Internal methods
    def _stress_responses(detection: EmotionDetection) → List[EmotionResponse]
    def _low_energy_responses(detection: EmotionDetection) → List[EmotionResponse]
    def _positive_mood_responses(detection: EmotionDetection) → List[EmotionResponse]
    def _negative_mood_responses(detection: EmotionDetection) → List[EmotionResponse]
    def _anxiety_responses(detection: EmotionDetection) → List[EmotionResponse]
```

**Example Usage:**

```python
from src.voice_sentiment import EmotionResponseEngine

engine = EmotionResponseEngine()

# Get recommendations for detected emotion
responses = engine.get_responses(detection)

for response in responses:
    print(f"[{response.priority.upper()}] {response.action}")
    print(f"  {response.description}")
    print(f"  Confidence: {response.confidence}")

# Output:
# [HIGH] reduce_meetings
#   Reduce your meetings load - reschedule non-urgent events to later this week
#   Confidence: 0.95
# [HIGH] schedule_break
#   Add a 30-minute break to decompress - go for a walk, meditate, or grab coffee
#   Confidence: 0.9
```

---

## Emotion Detection

### Detection Methods

**1. HuggingFace Transformers (ML-based)**

When available, uses state-of-the-art emotion classification:

```python
# Model: j-hartmann/emotion-english-distilroberta-base
# Emotions: joy, sadness, fear, anger, surprise, disgust, neutral

# Pros:
# - Highly accurate
# - Nuanced emotion detection
# - Context-aware

# Cons:
# - Requires transformer installation
# - Slower (~500ms per detection)
```

**2. Keyword-Based Fallback**

Built-in keyword dictionary for offline detection:

```python
# Keyword mappings
"stressed, overwhelmed, pressure, yoh" → STRESSED
"tired, exhausted, drained, burned out" → TIRED
"happy, great, amazing, love it" → HAPPY
"worried, anxious, nervous" → ANXIOUS
"frustrated, annoyed, angry" → FRUSTRATED

# Pros:
# - No dependencies
# - Very fast (~10ms)
# - Reliable for obvious emotions

# Cons:
# - Less nuanced
# - Requires exact keywords
```

### Stress Level Calculation

Stress determined by multiple factors:

```python
# 1. Emotion-based scores
if emotion in [STRESSED, ANXIOUS, FRUSTRATED]:
    score += 0.8
elif emotion in [TIRED, SAD]:
    score += 0.6
elif emotion in [CALM, HAPPY]:
    score = 0.0

# 2. Keyword indicators
if text contains ['urgent', 'asap', 'critical']:
    score += 0.3

# 3. Text intensity
if text.count('!') > 2:
    score += 0.2

# Final mapping
if score >= 0.8: CRITICAL
elif score >= 0.6: HIGH
elif score >= 0.4: MODERATE
else: LOW
```

### Energy Level Estimation

```python
EXCITED: 0.9
HAPPY, CALM: 0.7
NEUTRAL: 0.5
TIRED, SAD: 0.2
STRESSED, ANXIOUS: 0.4  # Stress uses energy
FRUSTRATED: 0.3
```

### Mood Calculation

```python
if emotion in [HAPPY, EXCITED] and stress == LOW:
    VERY_POSITIVE
elif emotion in [HAPPY, CALM]:
    POSITIVE
elif emotion in [NEUTRAL]:
    NEUTRAL
elif emotion in [STRESSED, ANXIOUS, FRUSTRATED]:
    if stress == CRITICAL: VERY_NEGATIVE
    elif stress == HIGH: NEGATIVE
    else: NEUTRAL
elif emotion in [TIRED, SAD]:
    NEGATIVE
```

---

## Response Types

### 1. Stress Responses

**When:** User is stressed (STRESS_LEVEL: HIGH or CRITICAL)

**Actions:**
- `reduce_meetings`: Reschedule non-urgent meetings
- `schedule_break`: Add decompression break (30 min)
- `reach_out`: Suggest contacting colleague for support
- `add_buffers`: Insert breathing room between meetings

**Example:**
```
Priority: HIGH
Action: reduce_meetings
Description: "Reduce your meetings load - reschedule non-urgent events 
             to later this week"
Confidence: 0.95
Rationale: "You sound stressed. A lighter calendar might help you regain control."
```

### 2. Low Energy Responses

**When:** Energy level < 0.3

**Actions:**
- `energy_boost`: Quick snack, walk, or exercise
- `reschedule_heavy_tasks`: Move demanding work to fresher times

**Example:**
```
Action: energy_boost
Description: "Light snack, short walk, or 5-minute exercise to boost energy"
Priority: MEDIUM
```

### 3. Positive Mood Responses

**When:** Mood is VERY_POSITIVE or POSITIVE

**Actions:**
- `plan_fun`: Add social events, hobbies, celebrations
- `tackle_hard_task`: Channel energy into challenging work

**Example:**
```
Action: plan_fun
Description: "Add something enjoyable to your calendar - social event, 
             hobby, or celebration"
Priority: LOW
Rationale: "Your positive energy is perfect for planning fun activities!"
```

### 4. Negative Mood Responses

**When:** Mood is NEGATIVE or VERY_NEGATIVE

**Actions:**
- `check_in`: Reach out to friend/colleague
- `comfort_activity`: Schedule self-care (meal, hobby, rest)

**Example:**
```
Action: check_in
Description: "Check in with a friend or colleague - you might benefit from a chat"
Priority: MEDIUM
```

### 5. Anxiety Responses

**When:** Emotion is ANXIOUS or CONFUSED

**Actions:**
- `create_structure`: Break day into manageable chunks
- `grounding_exercise`: 5-4-3-2-1 sensory exercise

**Example:**
```
Action: create_structure
Description: "Let's break down your day into clear, manageable chunks"
Priority: HIGH
Rationale: "Structure and clarity can reduce anxiety."
```

---

## Calendar Adjustments

### Stress Relief Plan

The module generates concrete calendar adjustments for stressed users:

```python
plan = engine.apply_stress_relief(events, detection)

# Output structure
{
    'stress_level': 'critical',
    'actions': [
        {
            'type': 'reschedule',
            'count': 3,
            'description': 'Reschedule 3 lower-priority items to reduce load',
            'items': ['Status Update', 'Optional Discussion', 'Planning Session']
        },
        {
            'type': 'add_buffers',
            'description': 'Add 15-minute buffers between meetings',
            'impact': 'Reduces back-to-back pressure'
        },
        {
            'type': 'add_break',
            'description': 'Add a 30-minute break block to decompress',
            'suggested_time': 'Mid-day or before your most stressful meeting'
        }
    ],
    'rationale': 'Based on your current stress level'
}
```

### Implementation Steps

```python
# 1. Detect emotion and stress
detection = analyzer.detect_emotion("I'm overwhelmed with meetings!")

# 2. If high stress, get adjustment plan
if detection.stress_level in [HIGH, CRITICAL]:
    events = get_calendar_events()
    plan = engine.apply_stress_relief(events, detection)
    
    # 3. Present to user
    print(f"Your stress level is {detection.stress_level.value}")
    print(f"I recommend:")
    for action in plan['actions']:
        print(f"  - {action['description']}")
    
    # 4. User confirms to apply
    # (Actual rescheduling would be done by calendar service)
```

---

## Voice Integration

### Voice Command Recognition

The voice handler recognizes emotion-related commands:

```python
# Pattern: "I'm {emotion} and {action}"
"I'm stressed, please shift my meetings to low load"
→ Command: 'mood-calendar-adjust'
→ Text: "I'm stressed, please shift my meetings..."

# Pattern: mood keyword + calendar action
"If stressed, reduce my meetings"
→ Command: 'mood-calendar-adjust'

# Pattern: ask for sentiment analysis
"How do I sound?"
→ Command: 'analyze-sentiment'
→ Text: (user repeats their concern)

# Pattern: detect and act
"I'm tired, add something fun on Saturday"
→ Command: 'mood-calendar-adjust'
→ Trigger: Happy mood → suggest fun activities
```

### Voice Patterns

```python
SENTIMENT_ANALYSIS_PATTERNS = [
    r"(?:detect|analyze)\s+(?:my\s+)?mood",
    r"(?:how\s+)?(?:do\s+)?(?:i|am\s+i)\s+(?:sound|seem|look)",
    r"stress\s+(?:check|level|analysis)",
    r"(?:am|i'm|i\s+am)\s+(?:stressed|tired|overwhelmed|anxious)",
]

MOOD_CALENDAR_PATTERNS = [
    r"(?:if\s+)?(?:i'm|i\s+am).*?(?:stressed|tired).*?(?:shift|move|reduce)",
    r"(?:if\s+)?(?:happy|excited).*?(?:add|schedule|plan).*?(?:fun|break)",
    r"(?:lighten|lower)\s+(?:my\s+)?(?:calendar|schedule)",
]
```

### Example Voice Workflow

```
User (stressed): "Yoh, I'm completely overwhelmed with meetings!"

1. Voice recognition captures: "Yoh, I'm completely overwhelmed..."

2. Command parser recognizes: 'mood-calendar-adjust'

3. Sentiment analyzer:
   - Detects: STRESSED, CRITICAL stress level
   - Mood: VERY_NEGATIVE
   - Energy: 0.2

4. Response engine generates:
   - Reduce meetings (HIGH confidence)
   - Add break (HIGH confidence)
   - Reach out for support (MEDIUM confidence)

5. Calendar service:
   - Identifies non-urgent meetings
   - Proposes rescheduling

6. Voice output:
   "I can hear you're really stressed right now. Let me help reduce 
    your meeting load. I found 3 non-urgent meetings we could reschedule 
    for next week. Should I go ahead?"
```

---

## API Endpoints

### POST /api/sentiment/analyze

Analyze emotion from text.

**Request:**
```json
{
  "text": "I'm so stressed with all these meetings!",
  "confidence_threshold": 0.5
}
```

**Response:**
```json
{
  "status": "success",
  "emotion": {
    "primary": "stressed",
    "secondary": [["anxious", 0.6], ["frustrated", 0.4]],
    "confidence": 0.9,
    "stress": "high",
    "mood": "negative",
    "energy": 0.3
  },
  "summary": "I detect you're feeling stressed, with hints of anxious. 
             Stress level: high. Energy: 30%.",
  "recommendations": [
    {
      "category": "calendar_adjustment",
      "action": "reduce_meetings",
      "description": "Reduce your meetings load...",
      "priority": "high",
      "confidence": 0.95,
      "rationale": "You sound stressed..."
    }
  ]
}
```

### POST /api/sentiment/mood-adjust

Adjust calendar based on mood.

**Request:**
```json
{
  "text": "I'm stressed, please lighten my calendar",
  "calendar_events": [
    {"title": "Meeting 1", "priority": "low"},
    {"title": "Meeting 2", "priority": "high"}
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "emotion": {
    "primary": "stressed",
    "stress": "critical",
    "mood": "very_negative"
  },
  "adjustment_plan": {
    "stress_level": "critical",
    "actions": [
      {
        "type": "reschedule",
        "count": 1,
        "description": "Reschedule 1 lower-priority item...",
        "items": ["Meeting 1"]
      },
      {
        "type": "add_buffers",
        "description": "Add 15-minute buffers..."
      }
    ]
  }
}
```

---

## Practical Examples

### Example 1: Stressed User

```python
# User says: "I have 8 meetings today and I'm really stressed"

# Detection
analyzer = VoiceSentimentAnalyzer()
detection = analyzer.detect_emotion("I have 8 meetings today and I'm really stressed")

# Results
# primary_emotion: STRESSED
# stress_level: CRITICAL
# mood: VERY_NEGATIVE
# energy_level: 0.2

# Recommendations
engine = EmotionResponseEngine()
responses = engine.get_responses(detection)

# Output recommendations:
# 1. [HIGH] Reduce meetings - reschedule non-urgent events
# 2. [HIGH] Add break - 30-minute decompression
# 3. [HIGH] Reach out - contact colleague for support

# Calendar adjustment
events = [
    {'title': 'Status Update', 'priority': 'low'},
    {'title': 'Important Meeting', 'priority': 'high'},
    {'title': 'Optional Discussion', 'priority': 'optional'}
]

plan = engine.apply_stress_relief(events, detection)
# Proposes: Reschedule Status Update and Optional Discussion
# Adds: 30-minute break before Important Meeting
```

### Example 2: Happy User

```python
# User says: "I'm so excited! Add something fun on Saturday!"

# Detection
detection = analyzer.detect_emotion("I'm so excited! Add something fun...")

# Results
# primary_emotion: EXCITED
# mood: VERY_POSITIVE
# energy_level: 0.9
# stress_level: LOW

# Recommendations
responses = engine.get_responses(detection)

# Output recommendations:
# 1. [LOW] Plan fun - add social events, hobbies, celebrations
# 2. [MEDIUM] Tackle hard task - channel energy into challenging work

# Voice response:
# "You sound great! I love your energy. Let me add some fun activities 
#  to your Saturday. How about: brunch with friends, hobby time, or 
#  something else you enjoy?"
```

### Example 3: Tired User

```python
# User says: "I'm exhausted and drained after this week"

# Detection
detection = analyzer.detect_emotion("I'm exhausted and drained after this week")

# Results
# primary_emotion: TIRED
# mood: NEGATIVE
# energy_level: 0.2
# stress_level: MODERATE

# Recommendations
responses = engine.get_responses(detection)

# Output recommendations:
# 1. [MEDIUM] Energy boost - snack, walk, exercise
# 2. [MEDIUM] Reschedule heavy tasks - move to when fresher

# Calendar adjustment
events = get_calendar_events()
# Identifies demanding tasks (design work, coding, presentations)
# Proposes: Move to Monday morning when energy is higher
# Suggests: Light tasks for Friday afternoon (emails, admin)
```

### Example 4: Anxious User

```python
# User says: "I don't know how to organize everything I need to do"

# Detection
detection = analyzer.detect_emotion("I don't know how to organize everything...")

# Results
# primary_emotion: ANXIOUS
# mood: NEGATIVE
# stress_level: HIGH

# Recommendations
responses = engine.get_responses(detection)

# Output recommendations:
# 1. [HIGH] Create structure - break day into manageable chunks
# 2. [MEDIUM] Grounding exercise - 5-4-3-2-1 sensory awareness

# Structure suggestion:
# "Let me help organize your day:
#  Morning (9-12): Deep work on main project
#  Lunch: Break
#  Afternoon (1-3): Meetings
#  Afternoon (3-5): Administrative tasks
#  This clear structure should help reduce the anxiety."
```

---

## Best Practices

### 1. Always Provide Context

More context = better analysis:

```python
# Poor: Just emotion word
text = "stressed"

# Better: Include reason
text = "I'm stressed about the presentation tomorrow"

# Best: Include intensity and context
text = "Yoh, I'm completely stressed with the presentation tomorrow and 
        I haven't even started!"
```

### 2. Use Threshold Appropriately

```python
# High threshold = only obvious emotions
detection = analyzer.detect_emotion(text, confidence_threshold=0.8)

# Low threshold = catch subtle emotions  
detection = analyzer.detect_emotion(text, confidence_threshold=0.3)

# Default = good balance
detection = analyzer.detect_emotion(text, confidence_threshold=0.5)
```

### 3. Combine with Other Data

```python
# Sentiment alone
detection = analyzer.detect_emotion(text)

# Combined with calendar data
stressed_and_overbooked = (
    detection.stress_level == CRITICAL and
    len(calendar_events) > 8
)

# Combined with time
end_of_week = datetime.now().weekday() >= 4  # Friday or later
weekend_approaching = end_of_week and detection.mood == NEGATIVE

# More accurate recommendations with context
if stressed_and_overbooked:
    # Definitely reduce calendar
    plan = engine.apply_stress_relief(events, detection)
```

### 4. Respect Privacy

```python
# Don't overanalyze or judge
# Provide supportive recommendations
# Offer choices rather than commands

# Good: "Would you like me to reduce your meeting load?"
# Bad: "You're too stressed to handle this."

# Good: "Your energy is low - want to add a break?"
# Bad: "You're lazy and tired."
```

### 5. Follow Up

```python
# After recommendations, check effectiveness
# Reschedule follow-up: "How are you feeling now?"

# Track patterns:
# - Same user stressed every Friday?
# - Particular meetings cause anxiety?
# - Energy drops after certain times?

# Adapt recommendations based on history
```

---

## Limitations & Considerations

### Current Limitations

- **Text-only analysis**: Doesn't process actual voice tone/pitch
  - Future: Extract prosody from audio
  
- **Context limitations**: Doesn't understand situational factors
  - Future: Calendar context integration
  
- **Single-language**: English only
  - Future: Multi-language support via translation
  
- **No persistence**: Doesn't remember emotional history
  - Future: Track emotional patterns over time

### Considerations for Deployment

1. **Sensitivity**: Some users may not want emotion analysis
   - Provide opt-out option
   - Be transparent about data usage

2. **Accuracy**: ML models may have biases
   - Test with diverse user groups
   - Provide manual override

3. **Recommendations**: Avoid over-intervention
   - Respect user autonomy
   - Offer suggestions, not mandates

4. **Privacy**: Emotional data is sensitive
   - Encrypt stored analyses
   - Don't share with third parties

---

## Advanced Features

### Pattern Recognition

Track emotional patterns:

```python
# Historical tracking (future enhancement)
history = [
    {'date': '2024-03-11', 'mood': 'negative', 'reason': 'too many meetings'},
    {'date': '2024-03-12', 'mood': 'positive', 'reason': 'focused work day'},
    {'date': '2024-03-13', 'mood': 'stressed', 'reason': 'deadline pressure'},
]

# Pattern detection
# "You're stressed every Wednesday before the big standup"
# → Recommend: schedule break before standup
```

### Predictive Recommendations

```python
# Based on patterns:
# "Friday afternoon - historically lower energy"
# → Suggest: light tasks for Friday PM

# "Monday mornings - high energy"
# → Suggest: schedule difficult meetings then
```

### Emotional Goal Setting

```python
# User goal: "I want to feel less stressed this week"

# Track daily emotion
# Provide recommendations
# Measure progress

# Output: "Great week! You were stressed only 1 day vs 3 last week"
```

---

## Integration Checklist

- [ ] Install HuggingFace transformers (optional but recommended)
- [ ] Add voice patterns for emotion commands
- [ ] Integrate with scheduler_handler.py
- [ ] Add API endpoints
- [ ] Test with diverse emotion expressions
- [ ] Document in web UI
- [ ] Add emotion visualization dashboard
- [ ] Create emotion history tracking

---

## Related Modules

- `src/voice_handler.py` - Voice command parsing
- `src/scheduler_handler.py` - Calendar integration
- `src/ai_scheduler.py` - Smart scheduling
- `src/email_drafter.py` - Email generation

---

## Summary

The Voice Sentiment module brings emotional intelligence to the calendar assistant. By detecting stress, energy levels, and mood, it enables truly empathetic scheduling and support.

**Quick Start:**
```python
from src.voice_sentiment import VoiceSentimentAnalyzer, EmotionResponseEngine

# Detect emotion
analyzer = VoiceSentimentAnalyzer(use_transformers=True)
detection = analyzer.detect_emotion("I'm so stressed!")

# Get recommendations
engine = EmotionResponseEngine()
responses = engine.get_responses(detection)

# Show to user
for r in responses:
    print(f"{r.action}: {r.description}")
```

For detailed integration, see `scheduler_handler.py` and `demo_scheduler.py`.
