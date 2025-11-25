Email Drafting & AI Communication Module
=========================================

Complete Guide to Smart Email Generation for Calendar Events

## Overview

The Email Drafting module (`src/email_drafter.py`) provides intelligent email generation for calendar events. It creates professional, contextual emails with customizable tone and type, making it easy to compose follow-ups, reminders, thank you notes, and more.

**Key Features:**
- 8 email types (THANK_YOU, REMINDER, FOLLOW_UP, CANCELLATION, etc.)
- 6 customizable tones (FORMAL, PROFESSIONAL, CASUAL, FRIENDLY, GRATEFUL, URGENT)
- 15+ built-in professional templates
- GPT-powered enhancement for naturalness
- Recipient-aware suggestions
- Confidence scoring
- Service-based architecture for easy integration

---

## Architecture

### Data Structures

```python
# Enums for email type and tone
EmailTone enum:
  - FORMAL: Highly professional, ceremonial language
  - PROFESSIONAL: Business-appropriate, polished
  - CASUAL: Relaxed, conversational tone
  - FRIENDLY: Warm, approachable, personable
  - GRATEFUL: Emphasizes appreciation and thanks
  - URGENT: Direct, time-sensitive, action-oriented

EmailType enum:
  - THANK_YOU: Gratitude for meeting/discussion
  - REMINDER: Proactive notification/reminder
  - FOLLOW_UP: Post-event with action items
  - CANCELLATION: Meeting cancellation notice
  - RESCHEDULE: Rescheduling notification
  - MEETING_NOTES: Meeting summary with notes
  - INVITATION: Event invitation
  - STATUS_UPDATE: Project/task status

# Data classes
EmailTemplate:
  - subject: str - Email subject line template
  - body: str - Email body template with {placeholders}
  - variables: List[str] - List of variable names to fill

DraftedEmail:
  - draft_id: str - Unique identifier for this draft
  - email_type: EmailType - Type of email
  - tone: EmailTone - Tone/style used
  - recipient: str - Email recipient address/name
  - subject: str - Final subject line
  - body: str - Final email body
  - event_title: str - Associated calendar event title
  - generated_at: datetime - When draft was created
```

### Core Classes

#### EmailTemplateLibrary

Provides built-in email templates for all type-tone combinations.

```python
class EmailTemplateLibrary:
    get_template(email_type: EmailType, tone: EmailTone) -> Optional[EmailTemplate]
    
# Usage
lib = EmailTemplateLibrary()
template = lib.get_template(EmailType.THANK_YOU, EmailTone.PROFESSIONAL)
```

**Built-in Templates:**

```
THANK_YOU Templates:
  ├─ FORMAL: "Dear {name}, I wanted to formally express..."
  ├─ PROFESSIONAL: "Thank you for taking the time to meet..."
  ├─ CASUAL: "Thanks so much for the chat earlier..."
  └─ GRATEFUL: "I'm truly grateful for your insights..."

REMINDER Templates:
  ├─ PROFESSIONAL: "Just a friendly reminder that..."
  ├─ CASUAL: "Hey! Just reminding you about..."
  └─ URGENT: "Important: Please remember that..."

FOLLOW_UP Templates:
  ├─ PROFESSIONAL: "Following up on our meeting..."
  └─ CASUAL: "Quick follow-up from our discussion..."

CANCELLATION Templates:
  └─ PROFESSIONAL: "I regret to inform you that I need to cancel..."
```

#### EventEmailDrafter

Main drafting engine that generates emails from calendar events.

```python
class EventEmailDrafter:
    def __init__(self, use_gpt: bool = False)
    
    # Main methods
    def draft_thank_you(event: Dict, recipient: str, tone: EmailTone) -> DraftedEmail
    def draft_reminder(event: Dict, recipient: str, tone: EmailTone) -> DraftedEmail
    def draft_follow_up(event: Dict, recipient: str, action_items: List[str], 
                       tone: EmailTone) -> DraftedEmail
    
    # Helpers
    def _extract_topic(event: Dict) -> str
    def _extract_time(time_str: str) -> str
    def _enhance_with_gpt(text: str, context: str) -> str
```

**Example Usage:**

```python
from src.email_drafter import EventEmailDrafter, EmailTone

# Initialize
drafter = EventEmailDrafter(use_gpt=True)

# Create event
event = {
    'summary': 'Product Strategy Meeting',
    'description': 'Discussed Q1 roadmap priorities',
    'start': {'dateTime': '2024-03-15T10:00:00'}
}

# Draft thank you email
drafted = drafter.draft_thank_you(
    event=event,
    recipient='alice@example.com',
    tone=EmailTone.PROFESSIONAL
)

print(drafted.subject)
# Output: "Thank You for Today's Product Strategy Meeting"

print(drafted.body)
# Output: "Hi Alice, Thank you for taking the time to meet with me 
#          today to discuss our Q1 product roadmap. I appreciated 
#          your insights on..."
```

#### EmailService

High-level API for email drafting and management.

```python
class EmailService:
    def __init__(self, email_drafter: EventEmailDrafter)
    
    # Core methods
    def draft_email(event: Dict, email_type: EmailType, recipient: str,
                   tone: Optional[EmailTone] = None) -> DraftedEmail
    def get_draft(draft_id: str) -> Optional[DraftedEmail]
    def list_drafts(email_type: Optional[EmailType] = None) -> List[DraftedEmail]
    def get_draft_text(draft_id: str, include_metadata: bool = False) -> str
    
    # Smart suggestions
    def suggest_email_type(event: Dict) -> str  # Returns email type suggestion
    def suggest_tone(recipient: str, event: Dict) -> str  # Returns tone suggestion
```

**Example Usage:**

```python
from src.email_drafter import EmailService, EmailType, EmailTone

# Initialize
drafter = EventEmailDrafter(use_gpt=True)
service = EmailService(drafter)

# Smart suggestions
suggested_type = service.suggest_email_type(event)
# Output: "thank_you"

suggested_tone = service.suggest_tone("ceo@company.com", event)
# Output: "formal"  (CEO suggests formal tone)

# Draft with suggestions
drafted = service.draft_email(
    event=event,
    email_type=EmailType.THANK_YOU,
    recipient='alice@example.com',
    tone=EmailTone.PROFESSIONAL
)

# Retrieve draft
retrieved = service.get_draft(drafted.draft_id)

# Get formatted text
text = service.get_draft_text(drafted.draft_id)
print(text)
# Output: "Subject: Thank You for Today's Meeting
#          
#          Hi Alice, Thank you for..."

# List all drafts
all_drafts = service.list_drafts()
thank_you_drafts = service.list_drafts(email_type=EmailType.THANK_YOU)
```

---

## Integration with Calendar Events

### Extracting Event Information

The module automatically extracts relevant information from Google Calendar events:

```python
# Calendar event structure
event = {
    'summary': 'Q4 Planning Meeting',  # Email topic
    'description': 'Discussed roadmap and budget',  # Email context
    'start': {'dateTime': '2024-03-15T10:00:00Z'},  # Time reference
    'end': {'dateTime': '2024-03-15T11:30:00Z'},    # Duration
    'attendees': [{'email': 'alice@example.com'}]   # Recipient
}

# Drafter extracts:
# - Topic: "Q4 Planning" (from summary)
# - Duration: "90 minutes" (from start/end)
# - Time: "March 15, 10:00 AM" (from datetime)
# - Context: "Discussed roadmap and budget" (from description)
```

### Smart Topic Extraction

```python
# The _extract_topic() method understands event context
"Team Sync Meeting" → "Team Synchronization"
"1:1 with Alice" → "One-on-one with Alice"
"Q4 Planning & Budget" → "Q4 Planning and Budget Discussion"
```

---

## Email Type Reference

### THANK_YOU
**When to use:** After a meeting or event to express gratitude.

```
Subject: Thank You for Today's {topic}
Body: Professional gratitude message with specific context
```

Example:
```
Subject: Thank You for Today's Strategy Discussion
Body: Hi Alice, Thank you for taking the time to meet with me today
      and sharing your insights on our product roadmap. Your perspective
      on market positioning was particularly valuable...
```

### REMINDER
**When to use:** Proactive notification before an upcoming event.

```
Subject: Reminder: {event} on {date}
Body: Friendly reminder with event details and timing
```

Example:
```
Subject: Reminder: Team Sync Tomorrow at 2 PM
Body: Hi Team, Just a friendly reminder that we have our weekly sync
      tomorrow at 2 PM in Conference Room B. Please come prepared
      to discuss your updates...
```

### FOLLOW_UP
**When to use:** Post-meeting with action items and next steps.

```
Subject: Follow-up: {topic} - Next Steps
Body: Summary of discussion + action items with owners
```

Example:
```
Subject: Follow-up: Q4 Planning - Next Steps
Body: Hi Team, Following up on our meeting yesterday. Here are the
      key action items:
      - Review budget proposals (Alice - by Friday)
      - Prepare roadmap doc (Bob - by next Monday)
      - Schedule stakeholder meeting (Charlie - this week)
```

### CANCELLATION
**When to use:** Notifying about a cancelled meeting.

```
Subject: Cancellation: {event}
Body: Professional apology and rescheduling offer
```

Example:
```
Subject: Cancellation: Product Planning Meeting
Body: Hi Alice, I regret to inform you that I need to cancel our
      scheduled product planning meeting on March 15 at 10 AM due
      to an urgent conflict. I sincerely apologize for any inconvenience.
      
      Would you be available to reschedule for later this week?
```

### RESCHEDULE
**When to use:** Moving a meeting to a new time.

```
Subject: Rescheduled: {event}
Body: New time and any special notes
```

### MEETING_NOTES
**When to use:** Sharing meeting summary and key points.

```
Subject: Notes from {event}
Body: Structured notes with decisions and action items
```

### INVITATION
**When to use:** Sending calendar event invitations.

```
Subject: Invitation: {event}
Body: Event details with date, time, location, and agenda
```

### STATUS_UPDATE
**When to use:** Project or task status communication.

```
Subject: Status Update: {project}
Body: Current status, progress, and blockers
```

---

## Tone Guide

### FORMAL
Professional, ceremonial language. Use for:
- Executive communications
- Important announcements
- Formal apologies or cancellations

```
"I would like to express my sincere gratitude for your invaluable 
contributions to our discussion today. Your insights have been most 
enlightening and have significantly enhanced my understanding..."
```

### PROFESSIONAL
Business-appropriate, polished tone. Use for:
- Most business communications
- Client interactions
- Standard meetings

```
"Thank you for taking the time to meet with me today. I appreciated 
your insights on our product strategy, and I'd like to follow up on 
the points we discussed..."
```

### CASUAL
Relaxed, conversational tone. Use for:
- Internal team communications
- Informal meetings
- Colleague interactions

```
"Thanks so much for the chat earlier! I really enjoyed discussing 
our ideas, and I think we're on the right track. Here's what we 
talked about..."
```

### FRIENDLY
Warm, approachable, personable tone. Use for:
- Building relationships
- Team morale
- Supportive communications

```
"Thanks for being such a great collaborator on this project! I 
really enjoyed working with you, and I'm excited about what we 
built together. Hope we can do this again soon!"
```

### GRATEFUL
Emphasizes appreciation and thanks. Use for:
- Expressing deep gratitude
- Acknowledging significant help
- Positive feedback

```
"I'm truly grateful for your generous support and guidance throughout 
this project. Your mentorship has been invaluable, and I genuinely 
appreciate everything you've done to help me succeed..."
```

### URGENT
Direct, time-sensitive, action-oriented. Use for:
- Critical communications
- Action-required messages
- Time-sensitive reminders

```
"URGENT: Please note the critical deadline change. The project 
deliverables are now due by Friday EOD instead of next Monday. 
Action required immediately."
```

---

## Voice Integration

### Voice Commands

The voice handler recognizes email-related commands:

```python
# Draft thank you email
"Draft a thank you email to Alice"
→ Returns: 'draft-email' command with email_type='thank_you'

# Draft reminder
"Write a reminder to the team"
→ Returns: 'draft-email' command with email_type='reminder'

# Draft follow-up
"Draft a follow-up email for tomorrow"
→ Returns: 'draft-email' command with email_type='follow_up'

# Compose email
"Compose an email to Bob"
→ Returns: 'draft-email' command with recipient='Bob'
```

### Voice Output

```python
# Get email as voice response
drafted_email = service.draft_email(event, EmailType.THANK_YOU, 'Alice')
voice_text = f"I've drafted a thank you email to Alice with subject: 
             '{drafted_email.subject}'. Should I send it?"
```

---

## API Endpoints

### POST /api/email/draft

Draft a new email.

**Request:**
```json
{
  "event": {
    "summary": "Team Sync",
    "description": "Weekly sync",
    "start": {"dateTime": "2024-03-15T10:00:00"}
  },
  "email_type": "thank_you",
  "recipient": "alice@example.com",
  "tone": "professional"
}
```

**Response:**
```json
{
  "status": "success",
  "draft_id": "draft_abc123",
  "type": "thank_you",
  "tone": "professional",
  "recipient": "alice@example.com",
  "subject": "Thank You for Today's Team Sync",
  "body": "Hi Alice, Thank you for...",
  "event_title": "Team Sync"
}
```

### GET /api/email/draft/{draft_id}

Retrieve a specific draft.

**Response:**
```json
{
  "status": "success",
  "draft_id": "draft_abc123",
  "type": "thank_you",
  "subject": "Thank You for Today's Team Sync",
  "body": "Hi Alice, Thank you for..."
}
```

### GET /api/email/drafts

List all drafts (optional filter by type).

**Query Parameters:**
- `type`: Optional email type filter

**Response:**
```json
{
  "status": "success",
  "count": 5,
  "drafts": [
    {
      "draft_id": "draft_1",
      "type": "thank_you",
      "recipient": "alice@example.com",
      "subject": "Thank You..."
    }
  ]
}
```

### GET /api/email/draft/{draft_id}/text

Get formatted draft text.

**Response:**
```
Subject: Thank You for Today's Team Sync

Hi Alice,

Thank you for taking the time to meet with me today...
```

### POST /api/email/suggest

Get suggestions for email type and tone.

**Request:**
```json
{
  "event": {
    "summary": "Meeting with CEO",
    "description": "Important strategy discussion"
  },
  "recipient": "ceo@company.com"
}
```

**Response:**
```json
{
  "status": "success",
  "suggested_type": "thank_you",
  "suggested_tone": "formal",
  "rationale": "CEO meeting suggests formal gratitude"
}
```

---

## Advanced Features

### GPT Enhancement

Enable GPT to improve naturalness and personalization:

```python
# Enable GPT during initialization
drafter = EventEmailDrafter(use_gpt=True)

# GPT will:
# - Improve language naturalness
# - Add personalization based on context
# - Optimize tone consistency
# - Enhance subject line appeal
```

### Confidence Scoring

All emails include confidence scores:

```python
drafted = service.draft_email(event, EmailType.THANK_YOU, 'Alice')
# drafted.confidence: 0.0-1.0 (internal tracking)
```

### Template Customization

Override default templates:

```python
custom_template = EmailTemplate(
    subject="Custom Thank You for {topic}",
    body="My custom template body...",
    variables=["topic", "name"]
)

# Templates can be registered in EmailTemplateLibrary
```

---

## Workflow Examples

### Example 1: Post-Meeting Follow-up

```python
# After calendar event
event = calendar_service.get_event('meeting_123')

# Suggest email type and tone
service = EmailService(EventEmailDrafter(use_gpt=True))
email_type = service.suggest_email_type(event)  # 'follow_up'
tone = service.suggest_tone('alice@example.com', event)  # 'professional'

# Draft follow-up with action items
drafted = service.draft_email(
    event=event,
    email_type=EmailType.FOLLOW_UP,
    recipient='alice@example.com',
    tone=EmailTone.PROFESSIONAL
)

# Get formatted text
email_text = service.get_draft_text(drafted.draft_id)

# Speaker: "I've drafted a follow-up email to Alice. Here's what it says:"
# [reads email]
```

### Example 2: Voice-Triggered Email

```python
# Voice command: "Draft a thank you email to Bob for the meeting"
# Parsed: 'draft-email' command with recipient='Bob'

# Scheduler handler
def handle_draft_email_command(params):
    event = get_last_calendar_event()  # Most recent event
    service = EmailService(EventEmailDrafter(use_gpt=True))
    
    drafted = service.draft_email(
        event=event,
        email_type=EmailType.THANK_YOU,
        recipient=params['recipient'],
        tone=EmailTone.PROFESSIONAL
    )
    
    # Speak response
    speak(f"I've drafted a thank you email to {params['recipient']}")
    speak(f"Subject: {drafted.subject}")
    speak(f"Ready to send?")
    
    return drafted
```

### Example 3: Batch Email Generation

```python
# Generate follow-ups for all meetings this week
from datetime import datetime, timedelta

service = EmailService(EventEmailDrafter(use_gpt=True))

week_start = datetime.now()
week_end = week_start + timedelta(days=7)

events = calendar_service.list_events(
    time_min=week_start,
    time_max=week_end
)

for event in events:
    drafted = service.draft_email(
        event=event,
        email_type=EmailType.FOLLOW_UP,
        recipient=event['attendees'][0]['email']
    )
    
    print(f"Drafted: {drafted.subject}")

# Output:
# Drafted: Follow-up: Team Sync - Next Steps
# Drafted: Follow-up: Product Planning - Next Steps
# Drafted: Follow-up: Strategy Discussion - Next Steps
```

---

## Best Practices

### 1. Tone Selection

**Choose based on relationship:**
- Executive/New contacts: FORMAL
- Colleagues/Known contacts: PROFESSIONAL
- Teammates: CASUAL or FRIENDLY
- Appreciation emphasis: GRATEFUL
- Time-critical: URGENT

### 2. Recipient Context

```python
# Let service suggest tone based on recipient
tone = service.suggest_tone(recipient_email, event)
# Service analyzes recipient domain:
# - "ceo@" → FORMAL
# - "colleague@" → PROFESSIONAL
# - "contractor@" → PROFESSIONAL
```

### 3. Action Items in Follow-ups

Always include specific action items:

```python
drafted = drafter.draft_follow_up(
    event=event,
    recipient='alice@example.com',
    action_items=[
        'Review budget proposal by Friday',
        'Schedule stakeholder meeting',
        'Prepare technical spec'
    ],
    tone=EmailTone.PROFESSIONAL
)
```

### 4. Keep Drafts Organized

```python
# List by type for easy review
thank_yous = service.list_drafts(email_type=EmailType.THANK_YOU)
follow_ups = service.list_drafts(email_type=EmailType.FOLLOW_UP)

# Review before sending
for draft in thank_yous:
    print(service.get_draft_text(draft.draft_id))
```

### 5. Use Event Context

The more event details provided, the better the email:

```python
# Good: Full event with description
event = {
    'summary': 'Product Planning',
    'description': 'Discussed Q1 roadmap, timeline, and resource allocation',
    'start': {'dateTime': '2024-03-15T10:00:00'},
    'end': {'dateTime': '2024-03-15T11:00:00'},
    'attendees': [{'email': 'alice@example.com'}]
}

# Better: Add custom context
event['custom_context'] = {
    'key_decisions': ['Approved Q1 roadmap', 'Allocated $500K budget'],
    'follow_up_required': True,
    'urgency': 'high'
}
```

---

## Error Handling

### Missing Event Information

```python
try:
    drafted = drafter.draft_thank_you(event, 'alice@example.com', tone)
except ValueError as e:
    print(f"Error: Missing event information - {e}")
    # Fall back to template
    template = lib.get_template(EmailType.THANK_YOU, EmailTone.PROFESSIONAL)
    drafted = DraftedEmail(
        draft_id=generate_id(),
        email_type=EmailType.THANK_YOU,
        tone=EmailTone.PROFESSIONAL,
        recipient='alice@example.com',
        subject=template.subject,
        body=template.body,
        event_title='Meeting'
    )
```

### GPT API Failures

```python
def _enhance_with_gpt(self, text, context):
    try:
        # Attempt GPT enhancement
        enhanced = openai.ChatCompletion.create(...)
        return enhanced
    except Exception as e:
        print(f"[WARN] GPT enhancement failed: {e}")
        # Fallback to template
        return text
```

---

## Performance Considerations

- Template library loads at initialization (minimal overhead)
- GPT enhancement adds ~500ms per email (optional)
- Drafts stored in memory (consider persistence for large volumes)
- Keyword extraction is O(1) operation

---

## Future Enhancements

- [ ] Email persistence to database
- [ ] Template learning from user edits
- [ ] A/B testing of email variants
- [ ] Recipient personality modeling
- [ ] Automatic send scheduling
- [ ] Multi-language support
- [ ] Email read tracking
- [ ] Template version control

---

## Related Modules

- `src/scheduler_handler.py` - Integration layer
- `src/voice_handler.py` - Voice command parsing
- `src/ai_scheduler.py` - Event scheduling
- `src/ai_chatgpt.py` - GPT integration

---

## Summary

The Email Drafting module provides a complete solution for intelligent, context-aware email generation. With 15+ built-in templates, 6 customizable tones, and smart suggestions, it enables professional email composition with minimal effort.

**Quick Start:**
```python
from src.email_drafter import EmailService, EventEmailDrafter, EmailType

service = EmailService(EventEmailDrafter(use_gpt=True))
drafted = service.draft_email(event, EmailType.THANK_YOU, 'alice@example.com')
print(drafted.subject)
print(drafted.body)
```

For detailed examples and integration code, see `demo_scheduler.py`.
