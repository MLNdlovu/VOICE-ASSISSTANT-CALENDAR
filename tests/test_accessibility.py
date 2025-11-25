"""
Unit Tests for Accessibility Enhancements

Tests for audio-only UI, voice error correction, adaptive speech rate,
and accessible voice summarization.
"""

import pytest
from datetime import datetime
from src.accessibility import (
    AccessibilityManager,
    AudioUIController,
    VoiceErrorCorrection,
    AccessibleVoiceSummarizer,
    AccessibilityMode,
    SpeechRate,
    AccessibilityState,
    UIElement
)


class TestAccessibilityState:
    """Test accessibility state management."""
    
    def test_default_state(self):
        """Test default accessibility state."""
        state = AccessibilityState()
        
        assert state.mode == AccessibilityMode.FULL_SCREEN
        assert state.speech_rate == SpeechRate.NORMAL
        assert state.use_audio_descriptions == True
        assert state.verbose_mode == False
    
    def test_state_modification(self):
        """Test modifying accessibility state."""
        state = AccessibilityState()
        
        state.mode = AccessibilityMode.AUDIO_ONLY
        state.speech_rate = SpeechRate.SLOW
        
        assert state.mode == AccessibilityMode.AUDIO_ONLY
        assert state.speech_rate == SpeechRate.SLOW


class TestAudioUIController:
    """Test audio UI controller."""
    
    def test_controller_initialization(self):
        """Test initializing audio UI."""
        controller = AudioUIController()
        
        assert controller is not None
        assert controller.current_view == "home"
    
    def test_set_accessibility_mode(self):
        """Test switching accessibility mode."""
        controller = AudioUIController()
        
        controller.set_accessibility_mode(AccessibilityMode.AUDIO_ONLY)
        assert controller.state.mode == AccessibilityMode.AUDIO_ONLY
        
        controller.set_accessibility_mode(AccessibilityMode.SCREEN_READER)
        assert controller.state.mode == AccessibilityMode.SCREEN_READER
    
    def test_set_speech_rate(self):
        """Test setting speech rate."""
        controller = AudioUIController()
        
        controller.set_speech_rate(SpeechRate.SLOW)
        assert controller.state.speech_rate == SpeechRate.SLOW
        
        controller.set_speech_rate(SpeechRate.FAST)
        assert controller.state.speech_rate == SpeechRate.FAST
    
    def test_adaptive_speech_rate_complex(self):
        """Test adaptive speech rate for complex content."""
        controller = AudioUIController()
        
        # Complex content (0.9 complexity)
        controller.adaptive_speech_rate(complexity=0.9)
        assert controller.state.speech_rate == SpeechRate.SLOW
        assert controller.state.reading_pace < 1.0
    
    def test_adaptive_speech_rate_simple(self):
        """Test adaptive speech rate for simple content."""
        controller = AudioUIController()
        
        # Simple content (0.1 complexity)
        controller.adaptive_speech_rate(complexity=0.1)
        assert controller.state.speech_rate == SpeechRate.FAST
        assert controller.state.reading_pace > 1.0
    
    def test_announce_element(self):
        """Test announcing UI element."""
        controller = AudioUIController()
        
        # Should not raise exception
        controller.announce_element(
            UIElement.BUTTON,
            "Schedule Event",
            "Press to schedule"
        )
    
    def test_navigate_to_screen(self):
        """Test navigating to screen."""
        controller = AudioUIController()
        
        controller.navigate_to_screen("calendar", "Your calendar for March 2024")
        
        assert controller.current_view == "calendar"
        assert len(controller.navigation_stack) > 0
    
    def test_navigate_back(self):
        """Test navigating back."""
        controller = AudioUIController()
        
        controller.navigate_to_screen("calendar", "Calendar")
        controller.navigate_to_screen("settings", "Settings")
        
        initial_view = controller.current_view
        controller.navigate_back()
        
        assert controller.current_view != initial_view
    
    def test_read_menu(self):
        """Test reading menu items."""
        controller = AudioUIController()
        
        menu_items = ["Schedule Meeting", "View Calendar", "Settings"]
        # Should not raise exception
        controller.read_menu(menu_items)
    
    def test_read_table(self):
        """Test reading table data."""
        controller = AudioUIController()
        
        headers = ["Time", "Event", "Duration"]
        rows = [
            ["10:00", "Team Meeting", "1 hour"],
            ["11:30", "One-on-one", "30 mins"]
        ]
        
        # Should not raise exception
        controller.read_table(headers, rows)


class TestVoiceErrorCorrection:
    """Test voice error correction."""
    
    def test_error_correction_initialization(self):
        """Test initializing error correction."""
        correction = VoiceErrorCorrection()
        
        assert correction is not None
        assert correction.last_commands == []
    
    def test_detect_correction_signal(self):
        """Test detecting correction signals."""
        correction = VoiceErrorCorrection()
        
        # Should detect corrections
        assert correction._is_correction_signal("Wait, no, 11:30") == True
        assert correction._is_correction_signal("Actually, tomorrow") == True
        assert correction._is_correction_signal("I mean 2 hours") == True
        
        # Should not detect as corrections
        assert correction._is_correction_signal("Schedule tomorrow") == False
        assert correction._is_correction_signal("Meeting at 2") == False
    
    def test_add_command_without_correction(self):
        """Test adding command without correction."""
        correction = VoiceErrorCorrection()
        
        result = correction.add_command("Schedule at 2pm")
        
        assert result['is_correction'] == False
        assert len(correction.last_commands) == 1
    
    def test_add_command_with_correction(self):
        """Test adding correction command."""
        correction = VoiceErrorCorrection()
        
        # Add initial command
        correction.add_command("Schedule at 11")
        # Add correction
        result = correction.add_command("Wait no, 11:30")
        
        assert result['is_correction'] == True
    
    def test_correction_extracts_change(self):
        """Test that correction extracts what changed."""
        correction = VoiceErrorCorrection()
        
        # Add initial
        correction.add_command("Book at 11 am")
        # Add correction
        result = correction.add_command("Actually 11:30")
        
        assert result['is_correction'] == True
        assert 'from' in result
        assert 'to' in result


class TestAccessibleVoiceSummarizer:
    """Test accessible voice summarization."""
    
    def test_summarizer_initialization(self):
        """Test initializing summarizer."""
        summarizer = AccessibleVoiceSummarizer(use_gpt=False)
        
        assert summarizer is not None
    
    def test_summarize_empty_agenda(self):
        """Test summarizing empty agenda."""
        summarizer = AccessibleVoiceSummarizer(use_gpt=False)
        
        summary = summarizer.summarize_agenda([], verbose=False)
        
        assert "no events" in summary.lower()
    
    def test_summarize_single_event(self):
        """Test summarizing single event."""
        events = [
            {'title': 'Team Meeting', 'start': '10:00'}
        ]
        
        summarizer = AccessibleVoiceSummarizer(use_gpt=False)
        summary = summarizer.summarize_agenda(events, verbose=False)
        
        assert "1" in summary
        assert "event" in summary.lower()
    
    def test_summarize_multiple_events_concise(self):
        """Test concise multi-event summary."""
        events = [
            {'title': 'Team Meeting', 'start': '10:00'},
            {'title': 'One-on-one', 'start': '11:30'},
            {'title': 'Review', 'start': '14:00'}
        ]
        
        summarizer = AccessibleVoiceSummarizer(use_gpt=False)
        summary = summarizer.summarize_agenda(events, verbose=False)
        
        assert "3" in summary
        assert "Team Meeting" in summary
    
    def test_summarize_multiple_events_verbose(self):
        """Test verbose multi-event summary."""
        events = [
            {'title': 'Team Meeting', 'start': '10:00'},
            {'title': 'One-on-one', 'start': '11:30'},
            {'title': 'Review', 'start': '14:00'}
        ]
        
        summarizer = AccessibleVoiceSummarizer(use_gpt=False)
        summary = summarizer.summarize_agenda(events, verbose=True)
        
        assert "3" in summary
        assert "Team Meeting" in summary
        assert "One-on-one" in summary
        assert "Review" in summary
    
    def test_summarize_event_details(self):
        """Test detailed event summary."""
        event = {
            'title': 'Project Planning',
            'start': '14:00',
            'duration_minutes': 90,
            'description': 'Quarterly planning session',
            'attendees': ['Alice', 'Bob', 'Charlie']
        }
        
        summarizer = AccessibleVoiceSummarizer(use_gpt=False)
        summary = summarizer.summarize_event_details(event)
        
        assert "Project Planning" in summary
        assert "14:00" in summary
        assert "90" in summary
        assert "3 participants" in summary or "Alice" in summary


class TestAccessibilityManager:
    """Test accessibility manager."""
    
    def test_manager_initialization(self):
        """Test initializing accessibility manager."""
        manager = AccessibilityManager()
        
        assert manager.audio_ui is not None
        assert manager.error_correction is not None
        assert manager.summarizer is not None
    
    def test_enable_audio_only_mode(self):
        """Test enabling audio-only mode."""
        manager = AccessibilityManager()
        
        manager.enable_audio_only_mode()
        assert manager.audio_ui.state.mode == AccessibilityMode.AUDIO_ONLY
    
    def test_enable_screen_reader_mode(self):
        """Test enabling screen reader mode."""
        manager = AccessibilityManager()
        
        manager.enable_screen_reader_mode()
        assert manager.audio_ui.state.mode == AccessibilityMode.SCREEN_READER
    
    def test_set_speech_rate(self):
        """Test setting speech rate through manager."""
        manager = AccessibilityManager()
        
        manager.set_speech_rate(SpeechRate.SLOW)
        assert manager.audio_ui.state.speech_rate == SpeechRate.SLOW
    
    def test_process_voice_command(self):
        """Test processing voice command."""
        manager = AccessibilityManager()
        
        result = manager.process_voice_command("Schedule tomorrow")
        
        assert 'command' in result
    
    def test_process_voice_command_with_correction(self):
        """Test processing corrected voice command."""
        manager = AccessibilityManager()
        
        # Add initial command
        manager.process_voice_command("Book at 11")
        # Add correction
        result = manager.process_voice_command("Wait no, 11:30")
        
        assert result.get('is_correction') == True
    
    def test_read_agenda(self):
        """Test reading agenda."""
        manager = AccessibilityManager()
        
        events = [
            {'title': 'Meeting 1', 'start': '10:00'},
            {'title': 'Meeting 2', 'start': '11:30'}
        ]
        
        # Should not raise exception
        manager.read_agenda(events, verbose=False)
    
    def test_describe_event(self):
        """Test describing event."""
        manager = AccessibilityManager()
        
        event = {
            'title': 'Team Sync',
            'start': '10:00',
            'duration_minutes': 60,
            'attendees': ['Alice', 'Bob']
        }
        
        # Should not raise exception
        manager.describe_event(event)


class TestAccessibilityIntegration:
    """Integration tests for accessibility features."""
    
    def test_blind_user_workflow(self):
        """Test workflow for blind user."""
        manager = AccessibilityManager()
        
        # Enable audio-only
        manager.enable_audio_only_mode()
        assert manager.audio_ui.state.mode == AccessibilityMode.AUDIO_ONLY
        
        # Set slow speech rate
        manager.set_speech_rate(SpeechRate.SLOW)
        
        # Read agenda
        events = [{'title': 'Meeting', 'start': '10:00'}]
        manager.read_agenda(events)
        
        # All operations succeeded
        assert True
    
    def test_error_correction_workflow(self):
        """Test error correction workflow."""
        manager = AccessibilityManager()
        
        # User says initial time
        r1 = manager.process_voice_command("Book at 11")
        
        # User corrects
        r2 = manager.process_voice_command("Actually wait, 11:30")
        
        assert r2.get('is_correction') == True
    
    def test_adaptive_speech_workflow(self):
        """Test adaptive speech rate workflow."""
        manager = AccessibilityManager()
        
        # Complex agenda
        manager.audio_ui.adaptive_speech_rate(complexity=0.8)
        rate = manager.audio_ui.state.speech_rate
        
        # Should be slow
        assert rate in [SpeechRate.SLOW, SpeechRate.VERY_SLOW]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
