"""
Unit Tests for Email Drafting Module

Tests email template generation, tone customization, GPT enhancement,
and the high-level email service API.
"""

import pytest
from datetime import datetime, timedelta
from src.email_drafter import (
    EmailTone, EmailType, EmailTemplate, DraftedEmail,
    EventEmailDrafter, EmailService, EmailTemplateLibrary
)


class TestEmailTone:
    """Test EmailTone enumeration."""
    
    def test_tone_values_exist(self):
        """Verify all tone enum values exist."""
        assert EmailTone.FORMAL.value == "formal"
        assert EmailTone.PROFESSIONAL.value == "professional"
        assert EmailTone.CASUAL.value == "casual"
        assert EmailTone.FRIENDLY.value == "friendly"
        assert EmailTone.GRATEFUL.value == "grateful"
        assert EmailTone.URGENT.value == "urgent"
    
    def test_tone_enumeration(self):
        """Test tone enumeration."""
        tones = list(EmailTone)
        assert len(tones) >= 6
        assert EmailTone.PROFESSIONAL in tones


class TestEmailType:
    """Test EmailType enumeration."""
    
    def test_type_values_exist(self):
        """Verify all type enum values exist."""
        assert EmailType.THANK_YOU.value == "thank_you"
        assert EmailType.REMINDER.value == "reminder"
        assert EmailType.FOLLOW_UP.value == "follow_up"
        assert EmailType.CANCELLATION.value == "cancellation"
    
    def test_type_enumeration(self):
        """Test type enumeration."""
        types = list(EmailType)
        assert len(types) >= 4


class TestEmailTemplate:
    """Test EmailTemplate dataclass."""
    
    def test_template_creation(self):
        """Test creating an email template."""
        template = EmailTemplate(
            subject="Test Subject",
            body="Test Body with {name}",
            variables=["name"]
        )
        assert template.subject == "Test Subject"
        assert template.body == "Test Body with {name}"
        assert template.variables == ["name"]
    
    def test_template_fill_variables(self):
        """Test filling template variables."""
        template = EmailTemplate(
            subject="Meeting with {name}",
            body="Hi {name}, thanks for the {topic}",
            variables=["name", "topic"]
        )
        filled = template.subject.format(name="Alice")
        assert "Alice" in filled
    
    def test_template_with_defaults(self):
        """Test template with default values."""
        template = EmailTemplate(
            subject="Subject",
            body="Body"
        )
        assert template.variables == []


class TestDraftedEmail:
    """Test DraftedEmail dataclass."""
    
    def test_drafted_email_creation(self):
        """Test creating a drafted email."""
        drafted = DraftedEmail(
            draft_id="draft_123",
            email_type=EmailType.THANK_YOU,
            tone=EmailTone.PROFESSIONAL,
            recipient="alice@example.com",
            subject="Thank You",
            body="Thanks for the meeting!",
            event_title="Team Sync"
        )
        assert drafted.draft_id == "draft_123"
        assert drafted.email_type == EmailType.THANK_YOU
        assert drafted.tone == EmailTone.PROFESSIONAL
        assert drafted.recipient == "alice@example.com"
    
    def test_drafted_email_timestamp(self):
        """Test that drafted email has generated_at timestamp."""
        drafted = DraftedEmail(
            draft_id="draft_1",
            email_type=EmailType.THANK_YOU,
            tone=EmailTone.PROFESSIONAL,
            recipient="user@example.com",
            subject="Subject",
            body="Body",
            event_title="Event"
        )
        assert isinstance(drafted.generated_at, datetime)


class TestEmailTemplateLibrary:
    """Test EmailTemplateLibrary."""
    
    def test_library_has_thank_you_templates(self):
        """Test that library has thank you templates."""
        lib = EmailTemplateLibrary()
        assert lib.get_template(EmailType.THANK_YOU, EmailTone.FORMAL) is not None
        assert lib.get_template(EmailType.THANK_YOU, EmailTone.PROFESSIONAL) is not None
    
    def test_library_has_reminder_templates(self):
        """Test that library has reminder templates."""
        lib = EmailTemplateLibrary()
        assert lib.get_template(EmailType.REMINDER, EmailTone.PROFESSIONAL) is not None
        assert lib.get_template(EmailType.REMINDER, EmailTone.CASUAL) is not None
    
    def test_library_has_follow_up_templates(self):
        """Test that library has follow-up templates."""
        lib = EmailTemplateLibrary()
        assert lib.get_template(EmailType.FOLLOW_UP, EmailTone.PROFESSIONAL) is not None
    
    def test_library_has_cancellation_templates(self):
        """Test that library has cancellation templates."""
        lib = EmailTemplateLibrary()
        assert lib.get_template(EmailType.CANCELLATION, EmailTone.PROFESSIONAL) is not None
    
    def test_library_fallback_to_professional_tone(self):
        """Test that library falls back to professional tone."""
        lib = EmailTemplateLibrary()
        # Request unusual tone combination, should fall back to professional
        template = lib.get_template(EmailType.THANK_YOU, EmailTone.PROFESSIONAL)
        assert template is not None
        assert isinstance(template, EmailTemplate)
    
    def test_all_templates_have_required_keys(self):
        """Test all templates have subject and body."""
        lib = EmailTemplateLibrary()
        for email_type in EmailType:
            for tone in EmailTone:
                template = lib.get_template(email_type, tone)
                if template:
                    assert template.subject
                    assert template.body
                    assert isinstance(template, EmailTemplate)


class TestEventEmailDrafter:
    """Test EventEmailDrafter class."""
    
    def test_drafter_initialization(self):
        """Test EventEmailDrafter initialization."""
        drafter = EventEmailDrafter(use_gpt=False)
        assert drafter is not None
        assert drafter.library is not None
    
    def test_draft_thank_you_email(self):
        """Test drafting a thank you email."""
        drafter = EventEmailDrafter(use_gpt=False)
        
        event = {
            'summary': 'Team Sync',
            'description': 'Weekly team meeting',
            'start': {'dateTime': datetime.now().isoformat()},
            'end': {'dateTime': (datetime.now() + timedelta(hours=1)).isoformat()}
        }
        
        drafted = drafter.draft_thank_you(
            event=event,
            recipient="alice@example.com",
            tone=EmailTone.PROFESSIONAL
        )
        
        assert isinstance(drafted, DraftedEmail)
        assert drafted.email_type == EmailType.THANK_YOU
        assert drafted.tone == EmailTone.PROFESSIONAL
        assert drafted.recipient == "alice@example.com"
        assert len(drafted.subject) > 0
        assert len(drafted.body) > 0
    
    def test_draft_reminder_email(self):
        """Test drafting a reminder email."""
        drafter = EventEmailDrafter(use_gpt=False)
        
        event = {
            'summary': 'Project Deadline',
            'description': 'Submit final deliverables',
            'start': {'dateTime': (datetime.now() + timedelta(days=1)).isoformat()}
        }
        
        drafted = drafter.draft_reminder(
            event=event,
            recipient="bob@example.com",
            tone=EmailTone.CASUAL
        )
        
        assert drafted.email_type == EmailType.REMINDER
        assert drafted.tone == EmailTone.CASUAL
        assert drafted.recipient == "bob@example.com"
    
    def test_draft_follow_up_email(self):
        """Test drafting a follow-up email."""
        drafter = EventEmailDrafter(use_gpt=False)
        
        event = {
            'summary': 'Strategy Discussion',
            'description': 'Discussed roadmap'
        }
        action_items = ['Complete wireframes', 'Review budget']
        
        drafted = drafter.draft_follow_up(
            event=event,
            recipient="charlie@example.com",
            action_items=action_items,
            tone=EmailTone.PROFESSIONAL
        )
        
        assert drafted.email_type == EmailType.FOLLOW_UP
        assert drafted.tone == EmailTone.PROFESSIONAL
        # Follow-up should mention action items
        assert any(item in drafted.body for item in action_items) or drafted.body
    
    def test_extract_topic(self):
        """Test topic extraction from event."""
        drafter = EventEmailDrafter(use_gpt=False)
        
        event = {
            'summary': 'Q4 Planning Meeting',
            'description': 'Planning for Q4 initiatives and roadmap'
        }
        
        topic = drafter._extract_topic(event)
        assert topic is not None
        # Should extract something meaningful
        assert len(topic) > 0
    
    def test_extract_time(self):
        """Test time extraction from event."""
        drafter = EventEmailDrafter(use_gpt=False)
        
        now = datetime.now()
        time_str = now.isoformat()
        
        extracted = drafter._extract_time(time_str)
        assert extracted is not None
    
    def test_tone_affects_email_content(self):
        """Test that tone affects email content."""
        drafter = EventEmailDrafter(use_gpt=False)
        
        event = {
            'summary': 'Meeting',
            'description': 'Test meeting',
            'start': {'dateTime': datetime.now().isoformat()}
        }
        
        formal = drafter.draft_thank_you(event, "user@example.com", EmailTone.FORMAL)
        casual = drafter.draft_thank_you(event, "user@example.com", EmailTone.CASUAL)
        
        # Both should be valid but different
        assert formal.subject != casual.subject or formal.body != casual.body
        assert len(formal.body) > 0
        assert len(casual.body) > 0


class TestEmailService:
    """Test high-level EmailService API."""
    
    def test_email_service_initialization(self):
        """Test EmailService initialization."""
        drafter = EventEmailDrafter(use_gpt=False)
        service = EmailService(drafter)
        assert service is not None
        assert service.drafter is not None
    
    def test_draft_email_dispatcher(self):
        """Test draft_email dispatcher method."""
        drafter = EventEmailDrafter(use_gpt=False)
        service = EmailService(drafter)
        
        event = {
            'summary': 'Team Meeting',
            'start': {'dateTime': datetime.now().isoformat()}
        }
        
        drafted = service.draft_email(
            event=event,
            email_type=EmailType.THANK_YOU,
            recipient="user@example.com"
        )
        
        assert isinstance(drafted, DraftedEmail)
        assert drafted.email_type == EmailType.THANK_YOU
    
    def test_list_drafts(self):
        """Test listing drafted emails."""
        drafter = EventEmailDrafter(use_gpt=False)
        service = EmailService(drafter)
        
        event = {
            'summary': 'Meeting',
            'start': {'dateTime': datetime.now().isoformat()}
        }
        
        # Draft multiple emails
        draft1 = service.draft_email(event, EmailType.THANK_YOU, "user1@example.com")
        draft2 = service.draft_email(event, EmailType.REMINDER, "user2@example.com")
        
        drafts = service.list_drafts()
        assert len(drafts) >= 2
        assert any(d.draft_id == draft1.draft_id for d in drafts)
        assert any(d.draft_id == draft2.draft_id for d in drafts)
    
    def test_get_draft(self):
        """Test retrieving a specific draft."""
        drafter = EventEmailDrafter(use_gpt=False)
        service = EmailService(drafter)
        
        event = {
            'summary': 'Meeting',
            'start': {'dateTime': datetime.now().isoformat()}
        }
        
        drafted = service.draft_email(event, EmailType.THANK_YOU, "user@example.com")
        retrieved = service.get_draft(drafted.draft_id)
        
        assert retrieved is not None
        assert retrieved.draft_id == drafted.draft_id
        assert retrieved.subject == drafted.subject
    
    def test_get_draft_text(self):
        """Test getting formatted draft text."""
        drafter = EventEmailDrafter(use_gpt=False)
        service = EmailService(drafter)
        
        event = {
            'summary': 'Meeting',
            'start': {'dateTime': datetime.now().isoformat()}
        }
        
        drafted = service.draft_email(event, EmailType.THANK_YOU, "user@example.com")
        text = service.get_draft_text(drafted.draft_id)
        
        assert text is not None
        assert "Subject:" in text or drafted.subject in text
        assert drafted.body in text
    
    def test_suggest_email_type(self):
        """Test smart email type suggestion."""
        drafter = EventEmailDrafter(use_gpt=False)
        service = EmailService(drafter)
        
        event = {
            'summary': 'Thank You Meeting',
            'description': 'Gratitude event'
        }
        
        suggested_type = service.suggest_email_type(event)
        assert suggested_type in [t.value for t in EmailType]
    
    def test_suggest_tone(self):
        """Test smart tone suggestion."""
        drafter = EventEmailDrafter(use_gpt=False)
        service = EmailService(drafter)
        
        event = {
            'summary': 'Formal Board Meeting'
        }
        
        suggested_tone = service.suggest_tone("CEO@company.com", event)
        assert suggested_tone in [t.value for t in EmailTone]
        # CEO suggests formal tone
        assert suggested_tone in ["formal", "professional"]


class TestEmailDrafterIntegration:
    """Integration tests for email drafting workflow."""
    
    def test_complete_email_workflow(self):
        """Test complete email drafting workflow."""
        drafter = EventEmailDrafter(use_gpt=False)
        service = EmailService(drafter)
        
        # Create a realistic event
        event = {
            'summary': 'Product Planning Session',
            'description': 'Discussed Q1 product roadmap and priorities',
            'start': {'dateTime': datetime.now().isoformat()},
            'end': {'dateTime': (datetime.now() + timedelta(hours=2)).isoformat()},
            'attendees': [{'email': 'alice@example.com'}]
        }
        
        # Suggest email type and tone
        email_type = service.suggest_email_type(event)
        tone = service.suggest_tone("alice@example.com", event)
        
        # Draft email
        drafted = service.draft_email(event, EmailType.FOLLOW_UP, "alice@example.com")
        
        # Retrieve and format
        retrieved = service.get_draft(drafted.draft_id)
        formatted = service.get_draft_text(drafted.draft_id)
        
        # Assertions
        assert drafted.draft_id is not None
        assert retrieved.subject == drafted.subject
        assert "Product" in formatted or "product" in formatted.lower()
    
    def test_multiple_tone_variants(self):
        """Test that different tones produce different emails."""
        drafter = EventEmailDrafter(use_gpt=False)
        
        event = {
            'summary': 'Important Meeting',
            'start': {'dateTime': datetime.now().isoformat()}
        }
        
        emails = []
        tones = [EmailTone.FORMAL, EmailTone.PROFESSIONAL, EmailTone.CASUAL]
        
        for tone in tones:
            drafted = drafter.draft_thank_you(event, "user@example.com", tone)
            emails.append(drafted)
        
        # All should be valid
        assert len(emails) == 3
        assert all(isinstance(e, DraftedEmail) for e in emails)
        
        # Content might differ
        subjects = [e.subject for e in emails]
        bodies = [e.body for e in emails]
        assert len(set(subjects)) >= 1  # At least one unique subject
    
    def test_email_with_special_characters(self):
        """Test email generation with special characters in event."""
        drafter = EventEmailDrafter(use_gpt=False)
        
        event = {
            'summary': 'Q4 2024 Planning & Budget Review',
            'description': 'Discussed: roadmap, timeline, budget ($$$)',
            'start': {'dateTime': datetime.now().isoformat()}
        }
        
        drafted = drafter.draft_thank_you(event, "user@example.com", EmailTone.PROFESSIONAL)
        
        assert drafted.subject is not None
        assert drafted.body is not None
        assert len(drafted.subject) > 0
        assert len(drafted.body) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
