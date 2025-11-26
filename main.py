import threading
import time
from src.voice_engine import get_voice_engine
from src.voice_handler import get_voice_command, speak, get_user_trigger, load_user_profile
from src.command_processor import CommandProcessor, CommandType
from src.voice_assistant_calendar import authenticate, config_command, load_voice_assistant_calendar
import sys

def handle_command(command):
    """
    Handle commands from the voice recognizer and routing to appropriate functionality.
    """
    cmd_type = command['type'] if isinstance(command, dict) else command.type
    params = command.get('parameters', {}) if isinstance(command, dict) else command.parameters
    # Implement handler logic for key command types
    if cmd_type == CommandType.BOOK_MEETING:
        summary = params.get('title', '')
        date = params.get('date', '')
        time_ = params.get('time', '')
        speak(f"Booking a meeting titled '{summary}' on {date} at {time_}.")
        # Here implement the actual booking logic using calendar api
    elif cmd_type == CommandType.LIST_EVENTS:
        filter_ = params.get('filter', 'today')
        speak(f"Listing your events for {filter_}.")
        # Implement event listing logic here
    elif cmd_type == CommandType.SET_REMINDER:
        title = params.get('title', 'Reminder')
        date = params.get('date', '')
        time_ = params.get('time', '')
        speak(f"Setting reminder '{title}' for {date} at {time_}.")
        # Implement reminder creation logic
    elif cmd_type == CommandType.SMALL_TALK:
        speak("I'm here to help! What do you want to do today?")
    elif cmd_type == CommandType.ASK_QUESTION:
        question = params.get('question', '') if isinstance(params, dict) else params
        speak("Sorry, I am not able to answer that yet.")
    else:
        speak("Sorry, I didn't understand that command.")

def main():
    print("Initializing Voice Assistant Calendar...")
    user_trigger = get_user_trigger()
    user_profile = load_user_profile(None) or {}
    user_name = user_profile.get('firstname', 'User')
    voice_engine = get_voice_engine(user_trigger, user_name)
    
    processor = CommandProcessor()
    # Register command handlers, we use a generic handler here
    def processor_handler(command):
        handle_command(command)
    for command_type in CommandType:
        processor.register_handler(command_type, processor_handler)
    
    # Start the voice engine active listening loop
    def on_command_recognized(text):
        command = processor.parse_command(text)
        processor.execute_command(command)
    
    voice_engine.on_command_recognized = on_command_recognized
    
    # Start listening for trigger phrase and commands
    voice_engine.start_active_listening()
    
    try:
        # Keep main thread alive while voice engine runs in background
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        voice_engine.stop_active_listening()
        print("\nVoice Assistant stopped.")
        sys.exit(0)

if __name__ == "__main__":
    main()
