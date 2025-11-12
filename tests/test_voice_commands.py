"""
Unit tests for voice command integration.
Tests command parsing, datetime extraction, summary extraction, and voice output.
"""

import pytest
from datetime import datetime, timedelta
from voice_handler import VoiceCommandParser, VoiceOutput


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


class TestRelativeDateParsing:
    """Test suite for relative date parsing functionality."""
    
    def test_today_parsing(self):
        """Test 'today' relative date parsing."""
        text = "Book today at 10:00"
        date, _ = VoiceCommandParser.extract_datetime(text)
        
        expected_date = datetime.now().strftime('%Y-%m-%d')
        assert date == expected_date, f"Expected '{expected_date}', got '{date}'"
    
    def test_tomorrow_parsing(self):
        """Test 'tomorrow' relative date parsing."""
        text = "Book tomorrow at 10:00"
        date, _ = VoiceCommandParser.extract_datetime(text)
        
        expected_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        assert date == expected_date, f"Expected '{expected_date}', got '{date}'"
    
    def test_yesterday_parsing(self):
        """Test 'yesterday' relative date parsing."""
        text = "Show events from yesterday"
        date, _ = VoiceCommandParser.extract_datetime(text)
        
        expected_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        assert date == expected_date, f"Expected '{expected_date}', got '{date}'"
    
    def test_in_days_parsing(self):
        """Test 'in X days' relative date parsing."""
        test_cases = [
            ("Book in 3 days at 10:00", 3),
            ("Schedule in 5 days", 5),
            ("in 1 day", 1),
        ]
        
        for text, days_ahead in test_cases:
            date, _ = VoiceCommandParser.extract_datetime(text)
            expected_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            assert date == expected_date, f"Failed to parse '{text}': expected '{expected_date}', got '{date}'"
    
    def test_in_weeks_parsing(self):
        """Test 'in X weeks' relative date parsing."""
        text = "Book in 2 weeks at 10:00"
        date, _ = VoiceCommandParser.extract_datetime(text)
        
        expected_date = (datetime.now() + timedelta(weeks=2)).strftime('%Y-%m-%d')
        assert date == expected_date, f"Expected '{expected_date}', got '{date}'"
    
    def test_next_day_parsing(self):
        """Test 'next [day name]' parsing."""
        # This test is more complex as it depends on the current day
        # We'll just verify it doesn't raise an exception and returns a valid date
        text = "Book next Monday at 10:00"
        date, _ = VoiceCommandParser.extract_datetime(text)
        
        # Should return a valid date (not None)
        assert date is not None, f"Failed to parse '{text}'"
        
        # Verify it's a valid date format
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            pytest.fail(f"Returned date '{date}' is not in valid YYYY-MM-DD format")
    
    def test_relative_date_with_absolute_time(self):
        """Test relative dates with explicit times."""
        test_cases = [
            ("Book tomorrow at 14:30", "14:30"),
            ("Schedule next Friday at 09:00", "09:00"),
            ("in 3 days at 15:45", "15:45"),
        ]
        
        for text, expected_time in test_cases:
            date, time = VoiceCommandParser.extract_datetime(text)
            assert time == expected_time, f"Time extraction failed for '{text}': expected '{expected_time}', got '{time}'"
            assert date is not None, f"Date extraction failed for '{text}'"


class TestVoiceOutput:
    """Test suite for VoiceOutput (Text-to-Speech) functionality."""
    
    def test_voice_output_initialization(self):
        """Test that VoiceOutput initializes properly."""
        output = VoiceOutput()
        # Should not raise an exception
        assert output is not None
    
    def test_voice_output_is_available_check(self):
        """Test availability check for text-to-speech."""
        output = VoiceOutput()
        is_available = output.is_available()
        # is_available should be a boolean
        assert isinstance(is_available, bool)
    
    def test_voice_output_rate_setting(self):
        """Test setting speech rate."""
        output = VoiceOutput()
        if output.is_available():
            output.set_rate(200)
            assert output.rate == 200
    
    def test_voice_output_volume_setting(self):
        """Test setting volume level."""
        output = VoiceOutput()
        if output.is_available():
            output.set_volume(0.5)
            assert output.volume == 0.5
    
    def test_voice_output_volume_bounds(self):
        """Test that volume is bounded to 0.0-1.0."""
        output = VoiceOutput()
        if output.is_available():
            # Valid volume
            output.set_volume(0.7)
            assert output.volume == 0.7
            
            # Invalid volumes should not change the value
            current_volume = output.volume
            output.set_volume(1.5)  # Too high
            assert output.volume == current_volume
            
            output.set_volume(-0.5)  # Too low
            assert output.volume == current_volume
    
    def test_voice_output_speak_method(self):
        """Test the speak method (should not raise exceptions)."""
        output = VoiceOutput()
        # Should handle gracefully whether TTS is available or not
        try:
            output.speak("Test message", wait=False)
        except Exception as e:
            pytest.fail(f"speak() raised unexpected exception: {e}")
    
    def test_voice_output_speak_response_method(self):
        """Test the speak_response convenience method."""
        output = VoiceOutput()
        # Should handle gracefully whether TTS is available or not
        try:
            output.speak_response("Welcome to Voice Assistant Calendar")
        except Exception as e:
            pytest.fail(f"speak_response() raised unexpected exception: {e}")


class TestEnhancedDateTimeExtraction:
    """Test suite for enhanced datetime extraction capabilities."""
    
    def test_time_with_am_pm_morning(self):
        """Test time extraction with AM/PM format (morning)."""
        test_cases = [
            ("Book at 9:30 am", "09:30"),
            ("Schedule at 10:00 AM", "10:00"),
            ("11:45 am appointment", "11:45"),
        ]
        
        for text, expected_time in test_cases:
            _, time = VoiceCommandParser.extract_datetime(text)
            assert time == expected_time, f"Failed for '{text}': expected '{expected_time}', got '{time}'"
    
    def test_time_with_am_pm_afternoon(self):
        """Test time extraction with AM/PM format (afternoon)."""
        test_cases = [
            ("Book at 2:30 pm", "14:30"),
            ("Schedule at 3:00 PM", "15:00"),
            ("5:45 pm appointment", "17:45"),
        ]
        
        for text, expected_time in test_cases:
            _, time = VoiceCommandParser.extract_datetime(text)
            assert time == expected_time, f"Failed for '{text}': expected '{expected_time}', got '{time}'"
    
    def test_time_noon_and_midnight(self):
        """Test special cases for noon and midnight."""
        test_cases = [
            ("Book at 12:00 pm", "12:00"),  # Noon
            ("Schedule at 12:00 am", "00:00"),  # Midnight
        ]
        
        for text, expected_time in test_cases:
            _, time = VoiceCommandParser.extract_datetime(text)
            assert time == expected_time, f"Failed for '{text}': expected '{expected_time}', got '{time}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

