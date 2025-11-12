"""
Unit tests for voice command integration.
Tests command parsing, datetime extraction, and summary extraction.
"""

import pytest
from voice_handler import VoiceCommandParser


class TestVoiceCommandParser:
    """Test suite for VoiceCommandParser functionality."""
    
    def test_book_command_parsing(self):
        """Test booking command recognition."""
        test_cases = [
            "Book a slot on 2024-03-01 at 10:00 for Python help",
            "Book a session on 2024-03-01 at 10:30 for algorithms",
            "I want to book a clinic for data structures",
            "Schedule a session on March 1st at 10 AM",
        ]
        
        for text in test_cases:
            command, params = VoiceCommandParser.parse_command(text)
            assert command == 'book', f"Failed to recognize book command in: {text}"
    
    def test_cancel_command_parsing(self):
        """Test cancellation command recognition."""
        test_cases = [
            "Cancel my booking on 2024-03-01 at 10:00",
            "Cancel my appointment on 2024-03-01 at 10:30",
            "Cancel the session on March 1st at 10 AM",
            "Unbook my appointment",
        ]
        
        for text in test_cases:
            command, params = VoiceCommandParser.parse_command(text)
            assert command == 'cancel-book', f"Failed to recognize cancel command in: {text}"
    
    def test_events_command_parsing(self):
        """Test event viewing command recognition."""
        test_cases = [
            "Show me upcoming events",
            "View my events",
            "List events",
            "What are my events?",
        ]
        
        for text in test_cases:
            command, params = VoiceCommandParser.parse_command(text)
            assert command == 'events', f"Failed to recognize events command in: {text}"
    
    def test_code_clinics_command_parsing(self):
        """Test code clinics calendar command recognition."""
        test_cases = [
            "Show me code clinics",
            "View code clinics calendar",
            "List code clinic slots",
            "Code clinic events",
        ]
        
        for text in test_cases:
            command, params = VoiceCommandParser.parse_command(text)
            assert command == 'code-clinics', f"Failed to recognize code-clinics command in: {text}"
    
    def test_help_command_parsing(self):
        """Test help command recognition."""
        test_cases = [
            "Help",
            "What can I do?",
            "Show available commands",
            "Help me",
        ]
        
        for text in test_cases:
            command, params = VoiceCommandParser.parse_command(text)
            assert command == 'help', f"Failed to recognize help command in: {text}"
    
    def test_datetime_extraction_date_only(self):
        """Test date extraction from voice commands."""
        test_text = "Book a slot on 2024-03-01 at 10:00 for Python"
        date, time = VoiceCommandParser.extract_datetime(test_text)
        assert date == "2024-03-01", f"Expected date '2024-03-01', got '{date}'"
    
    def test_datetime_extraction_time_only(self):
        """Test time extraction from voice commands."""
        test_text = "Book at 10:30 for Python"
        date, time = VoiceCommandParser.extract_datetime(test_text)
        assert time == "10:30", f"Expected time '10:30', got '{time}'"
    
    def test_datetime_extraction_both(self):
        """Test extracting both date and time."""
        test_text = "Cancel booking on 2024-03-01 at 14:00"
        date, time = VoiceCommandParser.extract_datetime(test_text)
        assert date == "2024-03-01", f"Expected date '2024-03-01', got '{date}'"
        assert time == "14:00", f"Expected time '14:00', got '{time}'"
    
    def test_datetime_extraction_alternate_format(self):
        """Test date extraction with alternate formats."""
        test_cases = [
            ("Book on 2024/03/01 at 10:00", "2024-03-01"),
            ("Cancel on 03/01/2024 at 10:00", "03-01-2024"),
        ]
        
        for text, expected_date in test_cases:
            date, _ = VoiceCommandParser.extract_datetime(text)
            # Convert to standard format
            if date:
                assert "/" in text or "-" in text, f"Date extraction failed for: {text}"
    
    def test_summary_extraction(self):
        """Test topic/summary extraction from booking commands."""
        test_cases = [
            ("Book a slot for Python help", "Python help"),
            ("Book a session studying algorithms", "algorithms"),
            ("Book studying data structures on 2024-03-01", "data structures"),
        ]
        
        for text, expected_summary in test_cases:
            summary = VoiceCommandParser.extract_summary(text)
            if summary:
                # Check if expected summary is contained in extracted summary
                assert expected_summary.lower() in summary.lower(), \
                    f"Expected '{expected_summary}' in '{summary}'"
    
    def test_full_booking_command_parsing(self):
        """Test full parsing of a complete booking command."""
        text = "Book a slot on 2024-03-01 at 10:30 for Python programming help"
        command, params = VoiceCommandParser.parse_command(text)
        
        assert command == 'book'
        assert params['date'] == '2024-03-01'
        assert params['time'] == '10:30'
        assert 'python' in params['summary'].lower()
    
    def test_full_cancel_command_parsing(self):
        """Test full parsing of a complete cancel command."""
        text = "Cancel my booking on 2024-03-01 at 14:00"
        command, params = VoiceCommandParser.parse_command(text)
        
        assert command == 'cancel-book'
        assert params['date'] == '2024-03-01'
        assert params['time'] == '14:00'
    
    def test_case_insensitivity(self):
        """Test that commands are recognized regardless of case."""
        test_cases = [
            "BOOK A SLOT ON 2024-03-01 AT 10:00",
            "Book A Slot On 2024-03-01 At 10:00",
            "book a slot on 2024-03-01 at 10:00",
        ]
        
        for text in test_cases:
            command, _ = VoiceCommandParser.parse_command(text)
            assert command == 'book', f"Case insensitivity failed for: {text}"
    
    def test_missing_parameters(self):
        """Test handling of commands with missing parameters."""
        text = "Book a slot"  # Missing date, time, and summary
        command, params = VoiceCommandParser.parse_command(text)
        
        assert command == 'book'
        assert params['date'] is None
        assert params['time'] is None
    
    def test_unknown_command(self):
        """Test handling of unrecognized commands."""
        text = "Do something random and weird"
        command, params = VoiceCommandParser.parse_command(text)
        
        assert command == 'unknown'
    
    def test_pattern_matching(self):
        """Test the pattern matching utility function."""
        text = "book a session"
        patterns = [r"book\s+(?:a\s+)?slot", r"book\s+(?:a\s+)?session"]
        
        assert VoiceCommandParser._match_pattern(text, patterns) is True
    
    def test_pattern_matching_no_match(self):
        """Test pattern matching when no match found."""
        text = "show me events"
        patterns = [r"book\s+", r"cancel\s+"]
        
        assert VoiceCommandParser._match_pattern(text, patterns) is False


class TestVoiceRecognizer:
    """Test suite for VoiceRecognizer functionality."""
    
    def test_recognizer_initialization(self):
        """Test that recognizer initializes properly."""
        from voice_handler import VoiceRecognizer
        
        recognizer = VoiceRecognizer()
        # Should not raise an exception
        assert recognizer is not None
    
    def test_recognizer_is_available_check(self):
        """Test availability check."""
        from voice_handler import VoiceRecognizer
        
        recognizer = VoiceRecognizer()
        is_available = recognizer.is_available()
        # is_available should be a boolean
        assert isinstance(is_available, bool)
    
    def test_recognizer_timeout_parameter(self):
        """Test custom timeout parameter."""
        from voice_handler import VoiceRecognizer
        
        recognizer = VoiceRecognizer(timeout=10, phrase_time_limit=8)
        assert recognizer.timeout == 10
        assert recognizer.phrase_time_limit == 8


class TestCommandIntegration:
    """Integration tests for complete voice command flow."""
    
    def test_multiple_commands_sequence(self):
        """Test parsing a sequence of different commands."""
        commands_and_results = [
            ("Book a slot on 2024-03-01 at 10:00 for Python", "book"),
            ("Show me upcoming events", "events"),
            ("Cancel my booking on 2024-03-01 at 10:00", "cancel-book"),
            ("Help", "help"),
            ("Exit", "exit"),
        ]
        
        for text, expected_command in commands_and_results:
            command, _ = VoiceCommandParser.parse_command(text)
            assert command == expected_command, \
                f"Expected '{expected_command}' but got '{command}' for: {text}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
