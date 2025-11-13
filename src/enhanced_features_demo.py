#!/usr/bin/env python3
"""
Demo Script for Voice Assistant Calendar Enhanced Features

This script demonstrates:
1. Voice output (text-to-speech)
2. Enhanced NLP parsing with relative dates
3. GUI dashboard
4. Voice command recognition

Run: python enhanced_features_demo.py
"""

import time
from voice_handler import VoiceOutput, VoiceCommandParser, VoiceRecognizer


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_voice_output():
    """Demonstrate text-to-speech capabilities."""
    print_section("1. VOICE OUTPUT (Text-to-Speech) DEMO")
    
    print("\nInitializing text-to-speech engine...")
    voice_output = VoiceOutput(rate=150, volume=0.9)
    
    if not voice_output.is_available():
        print("[WARN] Text-to-speech not available (pyttsx3 not installed)")
        print("    Install with: pip install pyttsx3")
        return
    
    print("[INFO] Text-to-speech engine ready!")
    
    # Demo 1: Basic speech
    print("\n[DEMO] Basic Speech")
    print("Speaking: 'Welcome to Voice Assistant Calendar'")
    voice_output.speak_response("Welcome to Voice Assistant Calendar")
    time.sleep(1)
    
    # Demo 2: Event confirmation
    print("\n[DEMO] Event Booking Confirmation")
    print("Speaking: 'Your Python help session has been booked for tomorrow at 2 PM'")
    voice_output.speak_response("Your Python help session has been booked for tomorrow at 2 PM")
    time.sleep(1)
    
    # Demo 3: Adjustable settings
    print("\n[DEMO] Adjustable Settings")
    print("Changing speech rate to 200 (faster)...")
    voice_output.set_rate(200)
    print("Speaking at faster rate: 'This is faster speech'")
    voice_output.speak_response("This is faster speech")
    time.sleep(1)
    
    print("\nChanging volume to 0.5...")
    voice_output.set_volume(0.5)
    print("Speaking at reduced volume: 'This is quieter'")
    voice_output.speak_response("This is quieter")
    time.sleep(1)


def demo_nlp_parsing():
    """Demonstrate enhanced NLP parsing with relative dates."""
    print_section("2. ENHANCED NLP PARSING DEMO")
    
    print("\nDemonstrating command parsing with relative dates...\n")
    
    test_commands = [
        # Absolute dates
        ("Book a slot on 2024-03-15 at 10:00 for Python help", "Absolute Date"),
        
        # Relative dates
        ("Book tomorrow at 2:30 PM for algorithms", "Relative Date (Tomorrow)"),
        ("Schedule in 3 days at 10:00 for database design", "Relative Date (in 3 days)"),
        ("Book next Monday at 14:00 for interview prep", "Relative Date (Day-based)"),
        ("Schedule today at 9:00 for quick sync", "Relative Date (Today)"),
        
        # Other commands
        ("Show me upcoming events", "View Events"),
        ("Cancel my booking on 2024-03-15 at 10:00", "Cancel Booking"),
        ("Help", "Help Command"),
    ]
    
    parser = VoiceCommandParser()
    
    for command_text, description in test_commands:
        print(f"[PARSE] {description}")
        print(f"   Input: \"{command_text}\"")
        
        command, params = parser.parse_command(command_text)
        
        print(f"   [SUCCESS] Parsed Command: {command}")
        if params:
            for key, value in params.items():
                if value is not None:
                    print(f"      - {key}: {value}")
        print()


def demo_datetime_extraction():
    """Demonstrate datetime extraction with various formats."""
    print_section("3. DATETIME EXTRACTION DEMO")
    
    print("\nDemonstrating date and time extraction from natural language...\n")
    
    test_cases = [
        # Absolute dates with times
        ("Book on 2024-03-15 at 10:30", "Absolute Date + Time"),
        ("Schedule on 03/15/2024 at 2:45 PM", "Alternate Date Format + AM/PM"),
        
        # Relative dates
        ("Book today at 9:00 AM", "Today"),
        ("Schedule tomorrow at 3:00 PM", "Tomorrow"),
        ("In 5 days at 11:00", "In X Days"),
        ("Next Friday at 14:00", "Next Day"),
        
        # Time formats
        ("Book at 9:30", "24-hour Format"),
        ("Schedule at 2:30 PM", "12-hour Format with PM"),
        ("Appointment at 11:45 AM", "12-hour Format with AM"),
    ]
    
    parser = VoiceCommandParser()
    
    for text, description in test_cases:
        print(f"[DATE] {description}")
        print(f"   Input: \"{text}\"")
        
        date, time = parser.extract_datetime(text)
        
        if date:
            print(f"   [SUCCESS] Date: {date}")
        else:
            print(f"   [WARN] Date: Not found")
        
        if time:
            print(f"   [SUCCESS] Time: {time}")
        else:
            print(f"   [WARN] Time: Not found")
        print()


def demo_voice_recognition():
    """Demonstrate voice recognition (optional)."""
    print_section("4. VOICE RECOGNITION DEMO (OPTIONAL)")
    
    print("\nChecking voice recognition availability...\n")
    
    recognizer = VoiceRecognizer()
    
    if recognizer.is_available():
        print("[INFO] Voice recognition is available!")
        print("\nTo test voice input, uncomment the code below:")
        print('''
        # Uncomment to test live voice input:
        # voice_text = recognizer.listen("Say: Book a slot tomorrow at 2 PM")
        # if voice_text:
        #     command, params = VoiceCommandParser.parse_command(voice_text)
        #     print(f"Command: {command}")
        #     print(f"Parameters: {params}")
        ''')
    else:
        print("[WARN] Voice recognition not available")
        print("   Install with: pip install SpeechRecognition pyaudio")


def demo_gui_preview():
    """Show GUI preview information."""
    print_section("5. GUI DASHBOARD PREVIEW")
    
    print("""
The Voice Assistant Calendar includes a modern GUI dashboard with:

FEATURES:
  * Event Display Table (next 7 events)
  * Real-time event refresh
  * Text-based event entry
  * Voice-based event booking
  * Event cancellation
  * Voice settings adjustment
  * Built-in help system

USAGE:
  1. Run: python voice_assistant_calendar.py
  2. Select: "gui" when prompted
  3. Use buttons to manage calendar

VOICE COMMANDS IN GUI:
  "Book on [date] at [time] for [topic]"
  "Show me upcoming events"
  "Cancel my booking on [date] at [time]"
  "Help"

SETTINGS:
  * Adjust speech rate (100-200 words/min)
  * Adjust volume (0.0-1.0)
  * Apply and save preferences

TABLE COLUMNS:
  * Date (YYYY-MM-DD)
  * Time (HH:MM)
  * Event Name
  * Creator Email

To launch the GUI:
  python voice_assistant_calendar.py
    """)


def demo_example_scenarios():
    """Demonstrate realistic usage scenarios."""
    print_section("6. REALISTIC USAGE SCENARIOS")
    
    print("""
SCENARIO 1: Scheduling a Study Session
════════════════════════════════════════════════════════════
User: "Book tomorrow at 2:30 PM for Python help"

Processing:
  Command: book
  Date: tomorrow → 2024-03-16
  Time: 2:30 PM → 14:30
  Topic: Python help

Result: Event scheduled for tomorrow at 2:30 PM
VoiceOutput: "Python help session booked for tomorrow at 2:30 PM!"


SCENARIO 2: Canceling a Booking
════════════════════════════════════════════════════════════
User: "Cancel my booking on March 20 at 10:00"

Processing:
  Command: cancel-book
  Date: 2024-03-20
  Time: 10:00

Result: Booking cancelled
VoiceOutput: "Event cancelled successfully!"

SCENARIO 3: Using Relative Dates
════════════════════════════════════════════════════════════
User: "Schedule in 5 days at 3 PM for data structures"

Processing:
  Command: book
  Date: in 5 days → 2024-03-21
  Time: 3 PM → 15:00
  Topic: data structures

Result: Event scheduled 5 days from today
VoiceOutput: "Data structures session scheduled!"

SCENARIO 4: Viewing Calendar
════════════════════════════════════════════════════════════
User: "Show me upcoming events"

Processing:
  Command: events

Result: Displays next 7 events in table format

Output:
  Date          Time     Event Name
  --────────────────────────────────────────────────────
  2024-03-15    10:00    Python Help
  2024-03-16    14:30    Data Structures
  2024-03-20    09:00    Interview Prep
    """)


def main():
    """Run all demos."""
    print("\n")
    print("=" * 70)
    print("         VOICE ASSISTANT CALENDAR")
    print("        Enhanced Features Demonstration")
    print("=" * 70)
    
    try:
        # Demo 1: Voice Output
        demo_voice_output()
        
        # Demo 2: NLP Parsing
        demo_nlp_parsing()
        
        # Demo 3: Datetime Extraction
        demo_datetime_extraction()
        
        # Demo 4: Voice Recognition
        demo_voice_recognition()
        
        # Demo 5: GUI Preview
        demo_gui_preview()
        
        # Demo 6: Realistic Scenarios
        demo_example_scenarios()
        
        # Conclusion
        print_section("[DEMO] COMPLETE")
        print("""
All features demonstrated successfully!

NEXT STEPS:
1. Run the full application:
   python voice_assistant_calendar.py

2. Choose your interface:
   - GUI (Graphical User Interface)
   - Voice (Voice Commands)
   - Text (Text Input)

3. Try these commands:
   - "Book tomorrow at 2 PM for Python"
   - "Show me upcoming events"
   - "Cancel my booking"

DOCUMENTATION:
- ENHANCED_FEATURES.md: Complete feature documentation
- VOICE_QUICK_START.md: Quick reference guide
- DEVELOPER_GUIDE.md: Technical implementation details

Happy scheduling!
        """)
        
    except Exception as e:
        print(f"\n[ERROR] Error during demo: {e}")
        import traceback
        traceback.print_exc()
if __name__ == "__main__":
    main()
