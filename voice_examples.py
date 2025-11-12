"""
Example usage and demonstrations of voice command functionality.
Run this file to see voice command parsing in action.
"""

from voice_handler import VoiceCommandParser, VoiceRecognizer


def demo_command_parsing():
    """Demonstrate various voice command parsing capabilities."""
    
    print("\n" + "="*70)
    print("VOICE COMMAND PARSING EXAMPLES")
    print("="*70)
    
    # Example commands from different categories
    examples = {
        "Booking Commands": [
            "Book a slot on 2024-03-01 at 10:00 for Python help",
            "Schedule a session on March 15th at 2:30 PM studying algorithms",
            "I want to book a code clinic for data structures",
            "Book a session at 10:30 for machine learning",
        ],
        "Cancellation Commands": [
            "Cancel my booking on 2024-03-01 at 10:00",
            "Unbook my appointment for today at 2 PM",
            "Cancel the session on March 1st at 10 AM",
        ],
        "View Commands": [
            "Show me upcoming events",
            "View code clinics calendar",
            "List available code clinic slots",
            "What are my upcoming events?",
        ],
        "Help and Configuration": [
            "Help",
            "Show available commands",
            "How do I share my calendar?",
            "Configure my settings",
        ],
        "Exit Commands": [
            "Exit",
            "Goodbye",
            "Quit the application",
        ],
    }
    
    parser = VoiceCommandParser()
    
    for category, commands in examples.items():
        print(f"\n{category}:")
        print("-" * 70)
        
        for cmd_text in commands:
            command, params = parser.parse_command(cmd_text)
            
            print(f"\n  Input:   \"{cmd_text}\"")
            print(f"  Command: {command}")
            
            if params and any(params.values()):
                print(f"  Params:")
                for key, value in params.items():
                    if value is not None:
                        print(f"    - {key}: {value}")
            else:
                print(f"  Params: (none)")


def demo_datetime_extraction():
    """Demonstrate datetime extraction from voice commands."""
    
    print("\n" + "="*70)
    print("DATETIME EXTRACTION EXAMPLES")
    print("="*70)
    
    test_cases = [
        "Book on 2024-03-01 at 10:00",
        "Cancel on March 1st at 2:30 PM",
        "Schedule on 2024/03/01 at 14:00",
        "Appointment at 10:30 today",
        "Meeting on 2024-12-25 at 09:00",
    ]
    
    print("\nExtracting dates and times from voice input:\n")
    
    for text in test_cases:
        date, time = VoiceCommandParser.extract_datetime(text)
        print(f"  Input: \"{text}\"")
        print(f"    Date: {date or 'Not found'}")
        print(f"    Time: {time or 'Not found'}")
        print()


def demo_summary_extraction():
    """Demonstrate topic/summary extraction from voice commands."""
    
    print("\n" + "="*70)
    print("SUMMARY/TOPIC EXTRACTION EXAMPLES")
    print("="*70)
    
    test_cases = [
        "Book a slot for Python help",
        "Book a session studying algorithms",
        "I want to book a clinic help with data structures",
        "Schedule a session about machine learning",
        "Book for web development project discussion",
    ]
    
    print("\nExtracting topics from booking commands:\n")
    
    for text in test_cases:
        summary = VoiceCommandParser.extract_summary(text)
        print(f"  Input:   \"{text}\"")
        print(f"  Summary: {summary or 'Not found'}")
        print()


def demo_microphone_status():
    """Check microphone and voice recognition availability."""
    
    print("\n" + "="*70)
    print("SYSTEM STATUS")
    print("="*70)
    
    recognizer = VoiceRecognizer()
    
    print(f"\nVoice Recognition Available: {recognizer.is_available()}")
    
    if recognizer.is_available():
        print("✅ Your system is ready for voice input!")
        print("\nYou can use the following voice commands:")
        print("  • 'python code_clinics_demo.py' to start the application")
        print("  • Choose 'voice' input when prompted")
        print("  • Speak your commands naturally")
    else:
        print("❌ Voice recognition is not available.")
        print("\nTo enable voice input:")
        print("  1. Install SpeechRecognition: pip install SpeechRecognition")
        print("  2. Install PyAudio: pip install pyaudio")
        print("  3. Connect a microphone")
        print("  4. Try again")


def demo_pattern_matching():
    """Demonstrate pattern matching capabilities."""
    
    print("\n" + "="*70)
    print("PATTERN MATCHING EXAMPLES")
    print("="*70)
    
    patterns = {
        "Book patterns": VoiceCommandParser.BOOK_PATTERNS,
        "Cancel patterns": VoiceCommandParser.CANCEL_PATTERNS,
        "Event patterns": VoiceCommandParser.EVENT_PATTERNS,
    }
    
    test_text = "Book a session"
    
    print(f"\nTesting: \"{test_text}\"")
    print("\nMatching patterns:\n")
    
    for pattern_name, pattern_list in patterns.items():
        is_match = VoiceCommandParser._match_pattern(test_text, pattern_list)
        status = "✓ MATCH" if is_match else "✗ NO MATCH"
        print(f"  {pattern_name:20} {status}")


def interactive_demo():
    """Interactive demonstration where user can test voice parsing."""
    
    print("\n" + "="*70)
    print("INTERACTIVE VOICE COMMAND TEST")
    print("="*70)
    
    parser = VoiceCommandParser()
    recognizer = VoiceRecognizer()
    
    print("\nThis demo allows you to test voice command parsing.")
    print("You can either:")
    print("  1. Speak a command (if microphone is available)")
    print("  2. Type a command")
    print("\nType 'quit' to exit the interactive demo.\n")
    
    while True:
        choice = input("Method [voice/text/quit]? ").strip().lower()
        
        if choice == 'quit':
            print("Exiting interactive demo.")
            break
        
        elif choice == 'voice':
            if recognizer.is_available():
                print("🎤 Listening for your voice command...")
                text = recognizer.listen()
                if text:
                    command, params = parser.parse_command(text)
                    print(f"\nCommand: {command}")
                    print(f"Parameters: {params}\n")
                else:
                    print("Could not recognize voice input. Try again.\n")
            else:
                print("Voice input not available. Use text mode instead.\n")
        
        elif choice == 'text':
            text = input("Enter voice command text: ").strip()
            if text:
                command, params = parser.parse_command(text)
                print(f"\nCommand: {command}")
                print(f"Parameters: {params}\n")
        
        else:
            print("Invalid choice. Please enter 'voice', 'text', or 'quit'.\n")


def main():
    """Run all demonstrations."""
    
    import sys
    
    print("\n╔════════════════════════════════════════════════════════════════════╗")
    print("║      VOICE COMMAND INTEGRATION - DEMONSTRATION AND EXAMPLES        ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        demo_type = sys.argv[1].lower()
        
        if demo_type == 'parsing':
            demo_command_parsing()
        elif demo_type == 'datetime':
            demo_datetime_extraction()
        elif demo_type == 'summary':
            demo_summary_extraction()
        elif demo_type == 'status':
            demo_microphone_status()
        elif demo_type == 'patterns':
            demo_pattern_matching()
        elif demo_type == 'interactive':
            interactive_demo()
        else:
            print(f"\nUnknown demo type: {demo_type}")
            print("Available demos: parsing, datetime, summary, status, patterns, interactive")
    else:
        # Run all demos
        demo_microphone_status()
        demo_command_parsing()
        demo_datetime_extraction()
        demo_summary_extraction()
        demo_pattern_matching()
        
        print("\n" + "="*70)
        print("INTERACTIVE TEST")
        print("="*70)
        try_interactive = input("\nWould you like to try interactive voice/text testing? [y/n] ").strip().lower()
        if try_interactive == 'y':
            interactive_demo()
    
    print("\n" + "="*70)
    print("For more information, see VOICE_INTEGRATION_GUIDE.md")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
