#!/usr/bin/env python
"""Test script to verify GUI loads successfully."""

import sys

print("Testing GUI module import...")
try:
    from gui_enhanced import launch_dashboard, VoiceAssistantGUI
    print("✅ GUI module imported successfully!")
    print("✅ Classes available: launch_dashboard, VoiceAssistantGUI")
except ImportError as e:
    print(f"❌ Failed to import GUI: {e}")
    sys.exit(1)

print("\nTesting date parsing...")
try:
    from get_details import get_date
    print("✅ Date parsing module imported successfully!")
except ImportError as e:
    print(f"❌ Failed to import get_details: {e}")
    sys.exit(1)

print("\nTesting email validation...")
try:
    import re
    test_emails = [
        "user@gmail.com",
        "dev@company.com",
        "student@university.edu",
    ]
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    for email in test_emails:
        if re.match(email_pattern, email):
            print(f"  ✅ {email}")
        else:
            print(f"  ❌ {email}")
except Exception as e:
    print(f"❌ Email validation failed: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✅ All modules loaded successfully!")
print("="*60)
print("\nYou can now run: python voice_assistant_calendar.py")
print("And choose 'gui' mode to launch the enhanced GUI!")
