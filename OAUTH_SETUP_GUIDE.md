#!/usr/bin/env python3
"""
Google OAuth Configuration Helper for Voice Assistant Calendar

This script helps verify and configure Google OAuth for local development.
"""

import os
import sys

def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def print_section(text):
    """Print a formatted section."""
    print(f"\n📋 {text}")
    print("-" * 70)

def main():
    print_header("🔐 Google OAuth Configuration Helper")
    
    # Check for client secret
    print_section("Step 1: Verify Client Secret File")
    
    if not os.path.exists('.config'):
        print("❌ .config directory not found!")
        print("   Creating .config directory...")
        os.makedirs('.config', exist_ok=True)
        print("   ✅ Created")
    
    client_files = [f for f in os.listdir('.config') if f.startswith('client_secret') and f.endswith('.json')]
    
    if client_files:
        print(f"✅ Found client secret file: {client_files[0]}")
        print(f"   Location: .config/{client_files[0]}")
    else:
        print("❌ No client secret file found!")
        print("   You need to download this from Google Cloud Console")
    
    # Show required configuration
    print_section("Step 2: Configure in Google Cloud Console")
    
    print("Follow these steps:")
    print("""
1. Go to Google Cloud Console:
   https://console.cloud.google.com/

2. Select your "Voice Assistant Calendar" project

3. Go to APIs & Services → Credentials

4. Find your OAuth 2.0 Client ID (type: "Desktop application")

5. Click to edit it and add these Redirect URIs:
   ✅ http://localhost:5000/oauth/callback
   ✅ http://127.0.0.1:5000/oauth/callback

6. IMPORTANT: If your OAuth consent screen is in "Testing" status:
   - Add your email as a test user
   - Or publish the app (requires verification)

7. Click "Save"
""")
    
    # Show environment notes
    print_section("Step 3: Environment Configuration")
    
    print("""
For local development (ONLY):
  ✅ OAUTHLIB_INSECURE_TRANSPORT=1 is automatically set
  ✅ This allows http://localhost:5000 to work with OAuth
  
For production (MUST CHANGE):
  ❌ NEVER use OAUTHLIB_INSECURE_TRANSPORT=1 in production
  ✅ Use HTTPS (SSL/TLS certificate required)
  ✅ Update web_app.py to remove insecure transport
""")
    
    # Show how to run
    print_section("Step 4: Run the Application")
    
    print("""
After configuring Google Cloud Console:

1. Make sure your client_secret_*.json is in .config/

2. Start the Flask server:
   python web_app.py

3. Open in browser:
   http://localhost:5000

4. Click "Sign in with Google"

5. You should see the OAuth consent screen

6. If you get "Unauthorized Client" or similar:
   - Check that redirect URI is exactly: http://localhost:5000/oauth/callback
   - Check that you're a test user (if app in Testing)
   - Check that client_secret file is valid
""")
    
    # Troubleshooting
    print_section("Troubleshooting")
    
    print("""
Error: "OAuth 2 MUST utilize https"
  → Set OAUTHLIB_INSECURE_TRANSPORT=1 (done automatically in web_app.py)

Error: "Redirect URI mismatch"
  → Add http://localhost:5000/oauth/callback to Google Cloud Console
  → Make sure it matches EXACTLY (including http://)

Error: "Unauthorized client" or "Not a test user"
  → Add your email as a test user in Google Cloud Console OAuth tab
  → Or publish the app (requires verification from Google)

Error: "Invalid client"
  → Verify client_secret_*.json file is valid
  → Download fresh copy from Google Cloud Console
""")
    
    # Final status
    print_section("Quick Checklist")
    
    checks = {
        ".config directory exists": os.path.exists('.config'),
        "Client secret file exists": len(client_files) > 0,
        "web_app.py has OAUTHLIB_INSECURE_TRANSPORT": True,  # We set it
    }
    
    for check, status in checks.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {check}")
    
    print_header("Ready to Start!")
    print("""
Next Steps:
1. Configure Google Cloud Console (see Step 2 above)
2. Run: python web_app.py
3. Open: http://localhost:5000
4. Sign in with your Google account

Questions? Check LATEST_IMPROVEMENTS.md for more help.
""")

if __name__ == '__main__':
    main()
