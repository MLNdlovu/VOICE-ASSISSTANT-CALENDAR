"""
AI Email/Message Drafting Module

Generates professional, contextual emails and messages based on calendar events.
Uses GPT for intelligent drafting with customizable tone and templates.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Any
import re

try:
    import openai
except ImportError:
    openai = None


# ============================================================================
# Data Structures & Enums
# ============================================================================

class EmailTone(Enum):
    """Email tone styles."""
    FORMAL = "formal"
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    GRATEFUL = "grateful"
    URGENT = "urgent"


class EmailType(Enum):
    """Types of emails to generate."""
    THANK_YOU = "thank_you"
    REMINDER = "reminder"
    FOLLOW_UP = "follow_up"
    CANCELLATION = "cancellation"
    RESCHEDULE = "reschedule"
    MEETING_NOTES = "meeting_notes"
    INVITATION = "invitation"
    STATUS_UPDATE = "status_update"


@dataclass
class EmailTemplate:
    """Email template with placeholders."""
    email_type: EmailType
    tone: EmailTone
    subject_template: str
    body_template: str
    description: str = ""
    variables: List[str] = field(default_factory=list)


@dataclass
class DraftedEmail:
    """An AI-generated email draft."""
    email_id: str
    email_type: EmailType
    tone: EmailTone
    recipient: str
    subject: str
    body: str
    event_title: str = ""
    event_date: Optional[datetime] = None
    confidence: float = 0.95
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.email_id,
            'type': self.email_type.value,
            'tone': self.tone.value,
            'recipient': self.recipient,
            'subject': self.subject,
            'body': self.body,
            'event': self.event_title,
            'confidence': self.confidence,
            'generated_at': self.generated_at.isoformat()
        }


# ============================================================================
# Email Templates
# ============================================================================

class EmailTemplateLibrary:
    """Built-in email templates for common scenarios."""
    
    TEMPLATES = {
        EmailType.THANK_YOU: {
            EmailTone.FORMAL: EmailTemplate(
                email_type=EmailType.THANK_YOU,
                tone=EmailTone.FORMAL,
                subject_template="Thank you for the {event_name}",
                body_template="""Dear {recipient},

Thank you for taking the time to meet with me regarding {event_name}.

I appreciated your insights and perspectives on {meeting_topic}. Your expertise was invaluable to our discussion.

I look forward to our continued collaboration.

Best regards,
{sender}""",
                variables=['event_name', 'recipient', 'meeting_topic', 'sender']
            ),
            EmailTone.PROFESSIONAL: EmailTemplate(
                email_type=EmailType.THANK_YOU,
                tone=EmailTone.PROFESSIONAL,
                subject_template="Thank you for the {event_name}",
                body_template="""Hi {recipient},

Thanks for taking the time to meet with me on {event_date}. I found our discussion about {meeting_topic} very helpful.

I'll make sure to follow up on the action items we discussed.

Best,
{sender}""",
                variables=['event_name', 'recipient', 'event_date', 'meeting_topic', 'sender']
            ),
            EmailTone.CASUAL: EmailTemplate(
                email_type=EmailType.THANK_YOU,
                tone=EmailTone.CASUAL,
                subject_template="Thanks for {event_name}!",
                body_template="""Hey {recipient},

Thanks for catching up on {event_date}! I really enjoyed chatting about {meeting_topic}.

Let me know if you need anything else!

Cheers,
{sender}""",
                variables=['event_name', 'recipient', 'event_date', 'meeting_topic', 'sender']
            ),
            EmailTone.GRATEFUL: EmailTemplate(
                email_type=EmailType.THANK_YOU,
                tone=EmailTone.GRATEFUL,
                subject_template="Thank you so much, {recipient}!",
                body_template="""Dear {recipient},

I'm truly grateful for the time you invested in our {event_name}. Your guidance on {meeting_topic} was incredibly valuable and has already given me clarity.

I deeply appreciate your generosity with your time and expertise.

With sincere thanks,
{sender}""",
                variables=['event_name', 'recipient', 'meeting_topic', 'sender']
            )
        },
        EmailType.REMINDER: {
            EmailTone.PROFESSIONAL: EmailTemplate(
                email_type=EmailType.REMINDER,
                tone=EmailTone.PROFESSIONAL,
                subject_template="Reminder: {event_name} - {event_time}",
                body_template="""Hi {recipient},

This is a friendly reminder about our {event_name} scheduled for {event_date} at {event_time}.

Looking forward to seeing you then.

Best regards,
{sender}""",
                variables=['event_name', 'recipient', 'event_date', 'event_time', 'sender']
            ),
            EmailTone.CASUAL: EmailTemplate(
                email_type=EmailType.REMINDER,
                tone=EmailTone.CASUAL,
                subject_template="Don't forget: {event_name} tomorrow!",
                body_template="""Hey {recipient},

Quick heads up - we've got {event_name} tomorrow at {event_time}. See you then!

{sender}""",
                variables=['event_name', 'recipient', 'event_time', 'sender']
            ),
            EmailTone.URGENT: EmailTemplate(
                email_type=EmailType.REMINDER,
                tone=EmailTone.URGENT,
                subject_template="REMINDER: {event_name} - {event_time}",
                body_template="""Hi {recipient},

Just a quick reminder that we have {event_name} scheduled for {event_date} at {event_time}.

Please confirm your attendance.

{sender}""",
                variables=['event_name', 'recipient', 'event_date', 'event_time', 'sender']
            )
        },
        EmailType.FOLLOW_UP: {
            EmailTone.PROFESSIONAL: EmailTemplate(
                email_type=EmailType.FOLLOW_UP,
                tone=EmailTone.PROFESSIONAL,
                subject_template="Follow-up: {event_name}",
                body_template="""Hi {recipient},

Following up on our {event_name} from {event_date}, I wanted to share some next steps:

{action_items}

Please let me know if you have any questions or would like to discuss further.

Best regards,
{sender}""",
                variables=['event_name', 'recipient', 'event_date', 'action_items', 'sender']
            ),
            EmailTone.CASUAL: EmailTemplate(
                email_type=EmailType.FOLLOW_UP,
                tone=EmailTone.CASUAL,
                subject_template="Quick follow-up on {event_name}",
                body_template="""Hey {recipient},

Quick follow-up from our chat on {event_date}. Here's what we discussed:

{action_items}

Let me know what you think!

Cheers,
{sender}""",
                variables=['event_name', 'recipient', 'event_date', 'action_items', 'sender']
            )
        },
        EmailType.CANCELLATION: {
            EmailTone.PROFESSIONAL: EmailTemplate(
                email_type=EmailType.CANCELLATION,
                tone=EmailTone.PROFESSIONAL,
                subject_template="Cancellation: {event_name}",
                body_template="""Hi {recipient},

I regret to inform you that I need to cancel our {event_name} scheduled for {event_date}.

{reason}

I apologize for any inconvenience this may cause. I'll be in touch to reschedule at your earliest convenience.

Best regards,
{sender}""",
                variables=['event_name', 'recipient', 'event_date', 'reason', 'sender']
            )
        }
    }
    
    @classmethod
    def get_template(cls, email_type: EmailType, tone: EmailTone) -> Optional[EmailTemplate]:
        """Get a template for the given type and tone."""
        if email_type in cls.TEMPLATES:
            if tone in cls.TEMPLATES[email_type]:
                return cls.TEMPLATES[email_type][tone]
            # Fallback to first available tone for this type
            if cls.TEMPLATES[email_type]:
                return list(cls.TEMPLATES[email_type].values())[0]
        return None


# ============================================================================
# Event Email Drafter
# ============================================================================

class EventEmailDrafter:
    """Generates emails based on calendar events."""
    
    def __init__(self, sender_name: str = "You", use_gpt: bool = False):
        self.sender_name = sender_name
        self.use_gpt = use_gpt and openai is not None
        self.draft_counter = 0
    
    def draft_thank_you(self, event: Dict[str, Any], recipient: str, 
                       tone: EmailTone = EmailTone.PROFESSIONAL) -> DraftedEmail:
        """
        Generate a thank you email for an event.
        
        Args:
            event: Calendar event dict with title, start_time, description
            recipient: Email recipient name
            tone: Email tone style
            
        Returns:
            DraftedEmail object
        """
        self.draft_counter += 1
        
        # Extract event details
        event_title = event.get('title', 'meeting')
        event_date = event.get('start_time', '')
        description = event.get('description', '')
        
        # Try to parse meaningful topic from title/description
        meeting_topic = self._extract_topic(event_title, description)
        
        # Get template
        template = EmailTemplateLibrary.get_template(EmailType.THANK_YOU, tone)
        if not template:
            template = EmailTemplateLibrary.get_template(
                EmailType.THANK_YOU, EmailTone.PROFESSIONAL
            )
        
        # Fill template
        subject = template.subject_template.format(
            event_name=event_title,
            recipient=recipient
        )
        
        body = template.body_template.format(
            recipient=recipient,
            event_name=event_title,
            event_date=event_date,
            meeting_topic=meeting_topic,
            sender=self.sender_name
        )
        
        # Enhance with GPT if available
        if self.use_gpt:
            body = self._enhance_with_gpt(body, tone)
        
        return DraftedEmail(
            email_id=f"draft_{self.draft_counter}",
            email_type=EmailType.THANK_YOU,
            tone=tone,
            recipient=recipient,
            subject=subject,
            body=body,
            event_title=event_title,
            confidence=0.95 if self.use_gpt else 0.85
        )
    
    def draft_reminder(self, event: Dict[str, Any], recipient: str,
                      tone: EmailTone = EmailTone.PROFESSIONAL) -> DraftedEmail:
        """Generate a reminder email for an event."""
        self.draft_counter += 1
        
        event_title = event.get('title', 'meeting')
        event_date = event.get('start_time', '')
        
        # Extract time
        event_time = self._extract_time(event_date)
        
        template = EmailTemplateLibrary.get_template(EmailType.REMINDER, tone)
        if not template:
            template = EmailTemplateLibrary.get_template(
                EmailType.REMINDER, EmailTone.PROFESSIONAL
            )
        
        subject = template.subject_template.format(
            event_name=event_title,
            event_time=event_time
        )
        
        body = template.body_template.format(
            recipient=recipient,
            event_name=event_title,
            event_date=event_date,
            event_time=event_time,
            sender=self.sender_name
        )
        
        if self.use_gpt:
            body = self._enhance_with_gpt(body, tone)
        
        return DraftedEmail(
            email_id=f"draft_{self.draft_counter}",
            email_type=EmailType.REMINDER,
            tone=tone,
            recipient=recipient,
            subject=subject,
            body=body,
            event_title=event_title,
            confidence=0.90
        )
    
    def draft_follow_up(self, event: Dict[str, Any], recipient: str,
                       action_items: List[str] = None,
                       tone: EmailTone = EmailTone.PROFESSIONAL) -> DraftedEmail:
        """Generate a follow-up email."""
        self.draft_counter += 1
        
        event_title = event.get('title', 'meeting')
        event_date = event.get('start_time', '')
        
        # Format action items
        if action_items:
            items_str = '\n'.join([f"• {item}" for item in action_items])
        else:
            items_str = "• Review meeting notes\n• Next steps TBD"
        
        template = EmailTemplateLibrary.get_template(EmailType.FOLLOW_UP, tone)
        if not template:
            template = EmailTemplateLibrary.get_template(
                EmailType.FOLLOW_UP, EmailTone.PROFESSIONAL
            )
        
        subject = template.subject_template.format(
            event_name=event_title
        )
        
        body = template.body_template.format(
            recipient=recipient,
            event_name=event_title,
            event_date=event_date,
            action_items=items_str,
            sender=self.sender_name
        )
        
        if self.use_gpt:
            body = self._enhance_with_gpt(body, tone)
        
        return DraftedEmail(
            email_id=f"draft_{self.draft_counter}",
            email_type=EmailType.FOLLOW_UP,
            tone=tone,
            recipient=recipient,
            subject=subject,
            body=body,
            event_title=event_title,
            confidence=0.92
        )
    
    def _extract_topic(self, title: str, description: str = "") -> str:
        """Extract meaningful topic from title and description."""
        # Remove common meeting prefixes
        topic = re.sub(r'^(meeting|call|sync|standup|1:1|discussion|sync-up)\s*:?\s*', 
                      '', title, flags=re.IGNORECASE).strip()
        
        if not topic:
            # Try to get first meaningful part of description
            if description:
                words = description.split()[:5]
                topic = ' '.join(words)
            else:
                topic = "our discussion"
        
        return topic[:80]  # Limit length
    
    def _extract_time(self, datetime_str: str) -> str:
        """Extract time from datetime string."""
        # Simple extraction - look for HH:MM pattern
        match = re.search(r'(\d{1,2}):(\d{2})', datetime_str)
        if match:
            return match.group(0)
        return "the scheduled time"
    
    def _enhance_with_gpt(self, body: str, tone: EmailTone) -> str:
        """Enhance email body with GPT."""
        try:
            tone_desc = {
                EmailTone.FORMAL: "formal and professional",
                EmailTone.PROFESSIONAL: "professional but friendly",
                EmailTone.CASUAL: "casual and warm",
                EmailTone.FRIENDLY: "warm and personable",
                EmailTone.GRATEFUL: "deeply grateful and appreciative",
                EmailTone.URGENT: "urgent and direct"
            }
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "user",
                    "content": f"Improve this email to be more {tone_desc.get(tone, 'professional')}. "
                              f"Keep it concise but engaging:\n\n{body}"
                }],
                max_tokens=300,
                temperature=0.7
            )
            return response['choices'][0]['message']['content'].strip()
        except Exception:
            return body


# ============================================================================
# Email Service
# ============================================================================

class EmailService:
    """High-level service for email drafting."""
    
    def __init__(self, sender_name: str = "You", use_gpt: bool = False):
        self.drafter = EventEmailDrafter(sender_name, use_gpt)
        self.drafts: Dict[str, DraftedEmail] = {}
    
    def draft_email(self, event: Dict[str, Any], recipient: str,
                   email_type: EmailType = EmailType.THANK_YOU,
                   tone: EmailTone = EmailTone.PROFESSIONAL,
                   **kwargs) -> DraftedEmail:
        """
        Draft an email for an event.
        
        Args:
            event: Calendar event dictionary
            recipient: Recipient name/email
            email_type: Type of email to draft
            tone: Tone of the email
            **kwargs: Additional parameters (action_items, reason, etc.)
            
        Returns:
            DraftedEmail object
        """
        if email_type == EmailType.THANK_YOU:
            draft = self.drafter.draft_thank_you(event, recipient, tone)
        elif email_type == EmailType.REMINDER:
            draft = self.drafter.draft_reminder(event, recipient, tone)
        elif email_type == EmailType.FOLLOW_UP:
            action_items = kwargs.get('action_items', [])
            draft = self.drafter.draft_follow_up(event, recipient, action_items, tone)
        else:
            # Default to thank you
            draft = self.drafter.draft_thank_you(event, recipient, tone)
        
        # Store draft
        self.drafts[draft.email_id] = draft
        return draft
    
    def get_draft(self, draft_id: str) -> Optional[DraftedEmail]:
        """Retrieve a saved draft."""
        return self.drafts.get(draft_id)
    
    def list_drafts(self) -> List[DraftedEmail]:
        """List all drafts."""
        return list(self.drafts.values())
    
    def get_draft_text(self, draft_id: str) -> str:
        """Get formatted draft for display/sending."""
        draft = self.get_draft(draft_id)
        if not draft:
            return "Draft not found"
        
        return f"""Subject: {draft.subject}

{draft.body}"""
    
    def suggest_email_type(self, event: Dict[str, Any]) -> EmailType:
        """
        Suggest email type based on event details.
        
        Args:
            event: Calendar event
            
        Returns:
            Suggested EmailType
        """
        title_lower = event.get('title', '').lower()
        description_lower = event.get('description', '').lower()
        
        # Check for keywords
        if any(word in title_lower for word in ['1:1', 'sync', 'meeting', 'call', 'discussion']):
            return EmailType.THANK_YOU
        
        if any(word in title_lower for word in ['reminder', 'follow', 'check-in']):
            return EmailType.REMINDER
        
        if any(word in description_lower for word in ['action', 'next steps', 'follow up']):
            return EmailType.FOLLOW_UP
        
        # Default
        return EmailType.THANK_YOU
    
    def suggest_tone(self, recipient: str = "", event: Dict[str, Any] = None) -> EmailTone:
        """
        Suggest appropriate tone based on context.
        
        Args:
            recipient: Recipient name
            event: Event details
            
        Returns:
            Suggested EmailTone
        """
        # Check recipient formality (simple heuristic)
        recipient_lower = recipient.lower()
        if any(title in recipient_lower for title in ['dr.', 'professor', 'executive']):
            return EmailTone.FORMAL
        
        # Check event urgency
        if event:
            title_lower = event.get('title', '').lower()
            if any(word in title_lower for word in ['urgent', 'critical', 'asap']):
                return EmailTone.URGENT
        
        # Default
        return EmailTone.PROFESSIONAL
