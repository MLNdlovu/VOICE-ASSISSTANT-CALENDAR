Demo instructions for Voice Assistant Calendar

Quick demo (no Google OAuth required)

1. Start the Flask server from the project root:

```powershell
cd "c:\Users\Lungelo Ndlovu\Documents\VOICE-ASSISSTANT-CALENDAR"
.\venv\Scripts\activate
python web_app.py
```

2. Run the demo script (PowerShell) to book and list demo events:

```powershell
cd "c:\Users\Lungelo Ndlovu\Documents\VOICE-ASSISSTANT-CALENDAR"
powershell -ExecutionPolicy Bypass -File .\scripts\demo_voice_simulate.ps1
```

What this does
- Uses the internal endpoint `/internal/voice_simulate` in demo mode (bypasses OAuth).
- Posts a booking command and then lists events for the requested day.
 - Stores demo events in-memory (no persistent calendar writes) by default. The demo now persists events to `.config/demo_events/<user>.json` so demo state survives server restarts.

Notes
- Demo events are now persisted to `.config/demo_events/<user>.json` so demo state survives server restarts.
- This demo is intended for local testing and development only. Do NOT expose `/internal/voice_simulate` in production.
- To simulate another user, change the `user_id` in the demo script to another `*@local` address.

Next steps
- To test full Google Calendar integration, configure a Google OAuth client and complete the OAuth flow via the app UI.
- To extend the demo, consider adding cancel/list filters or exporting demo events to a file.
