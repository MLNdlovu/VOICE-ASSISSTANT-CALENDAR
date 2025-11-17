"""Simple test script for text-to-speech (TTS)

Runs the project's voice_handler.speak() and reports availability.
"""
import time
import sys

import os
import pprint

print('CWD:', os.getcwd())
print('sys.path:')
pp = pprint.pformat(sys.path)
print(pp)

vh = None
try:
    import voice_handler as vh
    print('Imported voice_handler from root-level module')
except Exception as root_exc:
    print(f'Import voice_handler failed: {root_exc}')
    try:
        # Try importing from src package path by adding src to sys.path
        src_path = os.path.join(os.getcwd(), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        import voice_handler as vh
        print('Imported voice_handler from src/ after adding to sys.path')
    except Exception as e:
        print(f"Failed to import voice_handler (root and src attempts failed): {e}")
        sys.exit(2)

print("Checking TTS availability...")
try:
    available = vh.get_voice_output().is_available()
    print(f"TTS available: {available}")
except Exception as e:
    print(f"Error checking TTS availability: {e}")
    available = False

if available:
    try:
        print("Speaking test phrase...")
        vh.speak("This is a test of the Voice Assistant Calendar text to speech system.")
        time.sleep(1)
        print("Done speaking.")
    except Exception as e:
        print(f"Error during speak(): {e}")
else:
    print("pyttsx3 not available or failed to initialize. See requirements-voice.txt for installation.")

print("Test complete.")
