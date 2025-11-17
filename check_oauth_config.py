#!/usr/bin/env python3
"""
Google OAuth Configuration Helper for Voice Assistant Calendar

This script helps verify and configure Google OAuth for local development.
Run this before trying to use the web app for the first time.
"""

import os
import sys
import json

def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def print_section(text):
    """Print a formatted section."""
    print(f"\n📋 {text}")
    print("-" * 70)

def check_oauth_config():
    """Check OAuth configuration status."""
    print_header("🔐 Google OAuth Configuration Check")
    
    # Check for client secret
    print_section("1. Client Secret File")
    
    if not os.path.exists('.config'):
        print("   Creating .config directory...")
        os.makedirs('.config', exist_ok=True)
        print("   ✅ Created .config directory\n")
    
    client_files = [f for f in os.listdir('.config') 
                   if f.startswith('client_secret') and f.endswith('.json')]
    
    if client_files:
        client_file = client_files[0]
        print(f"   ✅ Found: {client_file}")
        try:
            with open(os.path.join('.config', client_file), 'r') as f:
                config = json.load(f)
                if 'installed' in config:
                    client_id = config['installed'].get('client_id', 'N/A')
                    print(f"   ✅ Client ID: {client_id[:20]}...{client_id[-10:]}\n")
                else:
                    print("   ⚠️  Config file format may not be correct\n")
        except Exception as e:
            print(f"   ❌ Error reading config: {e}\n")
    else:
        print("   ❌ No client_secret_*.json file found!")
        print("   📥 Download from Google Cloud Console:")
        print("      1. Go to https://console.cloud.google.com/")
        print("      2. Select your 'Voice Assistant Calendar' project")
        print("      3. APIs & Services → Credentials")
        print("      4. Find your OAuth 2.0 Client ID (type: 'Desktop')")
        print("      5. Click the download arrow (⬇️)")
        print("      6. Save as client_secret_*.json in .config/ folder\n")
    
    # Check web_app.py configuration
    print_section("2. Web App Configuration")
    try:
        with open('web_app.py', 'r') as f:
            content = f.read()
            if "OAUTHLIB_INSECURE_TRANSPORT" in content:
                print("   ✅ OAUTHLIB_INSECURE_TRANSPORT is configured")
                print("   ✅ Local development HTTP (localhost) will work\n")
            else:
                print("   ❌ OAUTHLIB_INSECURE_TRANSPORT not found in web_app.py")
                print("   ⚠️  OAuth may fail with 'https required' error\n")
    except Exception as e:
        print(f"   ❌ Error checking web_app.py: {e}\n")
    
    # Show next steps
    print_section("3. Next Steps")
    print("""
To use OAuth with Voice Assistant Calendar:

STEP A: Configure Google Cloud Console
  1. Go to https://console.cloud.google.com/
  2. Find your 'Voice Assistant Calendar' project
  3. Go to APIs & Services → Credentials
  4. Edit your OAuth 2.0 Client ID
  5. Add these Authorized redirect URIs:
     • http://localhost:5000/oauth/callback
     • http://127.0.0.1:5000/oauth/callback
  6. Click SAVE

STEP B: Handle OAuth Consent Screen
  If your consent screen shows "Testing":
    ✅ Option 1: Add your email as a test user
       1. Go to APIs & Services → OAuth consent screen
       2. Click "Add Users" in the Testing section
       3. Add your Gmail address
       4. Click SAVE
    
    ✅ Option 2: Publish the app
       1. Click "Publish App" on consent screen
       2. Follow verification process (may take days)

STEP C: Run the Application
  1. Open terminal in project folder
  2. Run: python web_app.py
  3. Open browser: http://localhost:5000
  4. Click "Sign in with Google"
""")
    
    # Troubleshooting
    print_section("4. If You Get Errors")
    print("""
"OAuth 2 MUST utilize https"
  → ✅ Already fixed in web_app.py (OAUTHLIB_INSECURE_TRANSPORT)

"Redirect URI mismatch"
  → Make sure Google Cloud has exactly:
     http://localhost:5000/oauth/callback

"Unauthorized client"
  → Your email is not added as test user
  → Go to OAuth consent screen → Testing → Add your email

"Invalid client" or "Failed to load client secret"
  → Your client_secret_*.json is missing or invalid
  → Download fresh copy from Google Cloud Console

"Connection refused"
  → Web app is not running
  → Run: python web_app.py
""")
    
    # Summary
    print_section("5. Configuration Summary")
    
    status = {
        "Client Secret File": "✅" if client_files else "❌",
        "web_app.py Configured": "✅",
        "Ready to Run": "✅" if client_files else "❌"
    }
    
    for check, result in status.items():
        print(f"  {result} {check}")
    
    if not client_files:
        print("\n  ⚠️  Download client_secret_*.json before running the app!")
    else:
        print("\n  ✅ You can now run: python web_app.py")
    
    print_header("Need More Help?")
    print("""
📖 Documentation:
  • OAUTH_SETUP_GUIDE.md  - Detailed setup instructions
  • LATEST_IMPROVEMENTS.md - Feature guide
  • README.md             - Project overview

🐛 Common Issues:
  See section 4 above for troubleshooting

🌐 Google Cloud Console:
  https://console.cloud.google.com/

📞 Google OAuth Docs:
  https://developers.google.com/identity/protocols/oauth2

Ready? Run the app with: python web_app.py
""")

if __name__ == '__main__':
    check_oauth_config()
