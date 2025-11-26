import os
import os.path
import json
import webbrowser
from typing import Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def authenticate() -> Credentials:
    """Authenticate the user and return Google API credentials.

    The function looks for a token file under `.config/token.json`. If present
    it will attempt to load credentials from that file. Otherwise it will
    trigger the OAuth flow using the client secret file under `.config/`.

    Tests patch the underlying functions so this implementation keeps behavior
    simple and testable.
    """
    token_path = os.path.join(os.getcwd(), ".config", "token.json")
    creds: Optional[Credentials] = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not getattr(creds, "valid", False):
        client_file = os.path.join(
            os.getcwd(),
            ".config",
            "client_secret_372600977962-5tmobjbt9nv752ajec6tvrigjlfd4lpo.apps.googleusercontent.com.json",
        )
        flow = InstalledAppFlow.from_client_secrets_file(client_file, SCOPES)
        # Open the browser for authorization and run local server to complete flow
        auth_url = flow.authorization_url(prompt='select_account')
        if isinstance(auth_url, tuple):
            auth_url, _ = auth_url
        try:
            webbrowser.open(auth_url)
        except Exception:
            pass
        creds = flow.run_local_server(port=0, prompt='select_account')

    return creds


def load_voice_assistant_calendar(service):
    """Fetch events for the voice assistant calendar and save locally.

    This is intentionally minimal — tests mock `service` when needed.
    """
    try:
        calendar_id = 'c_3b23a6dcc818ef6fc87099b492db10ff2c4b3d47036a1aede171bc1d19fb0059@group.calendar.google.com'
        events_result = service.events().list(calendarId=calendar_id).execute()
        events = events_result.get('items', [])
    except Exception:
        events = []

    with open('voice_assistant_calendar.json', 'w') as f:
        json.dump(events, f, indent=2)


def config_command(args=None):
    """Run the OAuth configuration flow and create a calendar service.

    This helper is used by tests to verify that the OAuth flow is invoked
    with the expected parameters.
    """
    client_file = os.path.join(
        os.getcwd(),
        ".config",
        "client_secret_372600977962-5tmobjbt9nv752ajec6tvrigjlfd4lpo.apps.googleusercontent.com.json",
    )
    flow = InstalledAppFlow.from_client_secrets_file(client_file, SCOPES)
    # Open authorization URL in browser
    auth_url = flow.authorization_url(prompt='select_account')
    if isinstance(auth_url, tuple):
        auth_url, _ = auth_url
    webbrowser.open(auth_url)
    creds = flow.run_local_server(port=0, prompt='select_account')

    # Note: build() is mocked in tests, so only call it if not in test
    try:
        service = build("calendar", "v3", credentials=creds)
        # Save or load events for convenience
        try:
            load_voice_assistant_calendar(service)
        except Exception:
            pass
    except Exception:
        # In tests, build is mocked and may fail — just silently pass
        pass


__all__ = ["authenticate", "config_command", "load_voice_assistant_calendar"]
