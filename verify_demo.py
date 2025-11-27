#!/usr/bin/env python
"""
Quick verification that all demo components are in place
"""

import os
import sys

print("🔍 VOICE ASSISTANT CALENDAR - DEMO VERIFICATION\n")

# Check 1: Template files
print("1. Checking template files...")
templates_needed = [
    'templates/voice_demo.html',
    'templates/auth.html',
    'templates/oauth_callback.html',
]

for tpl in templates_needed:
    exists = os.path.exists(tpl)
    status = "✅" if exists else "❌"
    print(f"   {status} {tpl}")

# Check 2: Python files
print("\n2. Checking Python modules...")
modules_needed = [
    'src/voice_blueprint.py',
    'web_app.py',
    'src/auth_blueprint.py',
]

for mod in modules_needed:
    exists = os.path.exists(mod)
    status = "✅" if exists else "❌"
    print(f"   {status} {mod}")

# Check 3: Google credentials
print("\n3. Checking Google credentials...")
config_exists = os.path.exists('.config/client_secret_*.json')
config_files = [f for f in os.listdir('.config') if f.startswith('client_secret') and f.endswith('.json')]
if config_files:
    print(f"   ✅ Found {len(config_files)} client secret file(s)")
    for f in config_files:
        print(f"      - {f}")
else:
    print("   ❌ No client_secret_*.json found in .config/")

# Check 4: Try importing
print("\n4. Checking Python imports...")
try:
    from src.voice_blueprint import voice_bp
    print("   ✅ voice_blueprint imports successfully")
except Exception as e:
    print(f"   ❌ voice_blueprint import failed: {e}")

try:
    from src.auth_blueprint import auth_bp
    print("   ✅ auth_blueprint imports successfully")
except Exception as e:
    print(f"   ❌ auth_blueprint import failed: {e}")

try:
    import web_app
    print("   ✅ web_app imports successfully")
except Exception as e:
    print(f"   ❌ web_app import failed: {e}")

# Check 5: Check for Flask
print("\n5. Checking dependencies...")
try:
    import flask
    print(f"   ✅ Flask {flask.__version__} installed")
except:
    print("   ❌ Flask not installed")

try:
    import google.auth
    print("   ✅ google.auth installed")
except:
    print("   ❌ google.auth not installed")

try:
    import google_auth_oauthlib
    print("   ✅ google_auth_oauthlib installed")
except:
    print("   ❌ google_auth_oauthlib not installed")

print("\n✅ DEMO VERIFICATION COMPLETE")
print("\nTo start the demo:")
print("  1. python web_app.py")
print("  2. Open http://localhost:5000")
print("  3. Login with Google")
print("  4. Set your profile (Name, Trigger)")
print("  5. Say 'Book an event' to start demo")
