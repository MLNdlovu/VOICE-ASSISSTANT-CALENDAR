# Integration test script (not using pytest) to simulate login and profile completion
# Usage: python tests/integration_test_voice.py

import os
import json
from pprint import pprint

from web_app import app


def run():
    with app.test_client() as client:
        # Simulate a logged in session
        with client.session_transaction() as sess:
            sess['access_token'] = 'test-token'
            sess['user_email'] = 'test.user@example.com'

        # Complete profile POST
        payload = {
            'firstname': 'Test',
            'lastname': 'User',
            'trigger': 'TU01',
            'email': 'test.user@example.com'
        }
        resp = client.post('/api/complete-profile', json=payload)
        print('POST /api/complete-profile ->', resp.status_code)
        try:
            print(resp.get_json())
        except Exception:
            print(resp.data)

        # Verify profile file persisted
        profile_path = os.path.join('.config', 'profiles', f"{payload['email']}.json")
        print('Expected profile path:', profile_path)
        if os.path.exists(profile_path):
            print('Profile file exists. Contents:')
            with open(profile_path, 'r', encoding='utf-8') as pf:
                pprint(json.load(pf))
        else:
            print('Profile file NOT found.')

        # Try to open unified dashboard
        resp2 = client.get('/unified')
        print('\nGET /unified ->', resp2.status_code)
        if resp2.status_code == 200:
            print('Unified dashboard rendered (truncated):')
            print(resp2.get_data(as_text=True)[:500])
        else:
            print('Unified dashboard not available; response length:', len(resp2.data))

        # Call voice start endpoint
        resp3 = client.post('/api/voice/start')
        print('\nPOST /api/voice/start ->', resp3.status_code)
        try:
            print(resp3.get_json())
        except Exception:
            print(resp3.data)

        # Test parsing of a booking voice command via /api/voice/process-command
        test_text = 'Book a meeting tomorrow at 10:00 for Testing'
        resp4 = client.post('/api/voice/process-command', json={'text': test_text})
        print('\nPOST /api/voice/process-command ->', resp4.status_code)
        try:
            j = resp4.get_json()
            pprint(j)
            # Basic validation
            assert resp4.status_code == 200
            assert j.get('success') is True
            assert j.get('command_type') in ('book_meeting', 'list_events', 'set_reminder', 'ask_question', 'none')
            print('\nProcess-command parsing OK')
        except AssertionError:
            print('Process-command assertions failed')
        except Exception:
            print(resp4.data)

        # --- Test /api/book endpoint with a fake calendar service to avoid real Google API calls ---
        # Provide minimal fake service expected by src.book.create_event_user
        class FakeEvents:
            def insert(self, calendarId=None, body=None):
                class _Exec:
                    def execute(self_inner):
                        return {'id': 'fake-event-123'}
                return _Exec()

        class FakeService:
            def events(self):
                return FakeEvents()

        # Monkeypatch web_app.get_calendar_service to return our fake service
        import web_app
        web_app.get_calendar_service = lambda access_token=None: FakeService()

        # Prepare a valid booking payload
        from datetime import datetime, timedelta
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        booking_payload = {
            'email': 'test.user@example.com',
            'date': tomorrow,
            'time': '10:00',
            'summary': 'Integration Test Booking',
            'duration': 30
        }

        resp5 = client.post('/api/book', json=booking_payload)
        print('\nPOST /api/book ->', resp5.status_code)
        try:
            j5 = resp5.get_json()
            pprint(j5)
            assert resp5.status_code == 200
            assert j5.get('success') is True
            print('Create event (fake service) OK')
        except AssertionError:
            print('Booking assertions failed')
        except Exception:
            print(resp5.data)

        # Test missing fields
        resp6 = client.post('/api/book', json={'email': 'a@b.com'})
        print('\nPOST /api/book missing fields ->', resp6.status_code)
        try:
            assert resp6.status_code == 400
            print('Missing fields correctly returned 400')
        except AssertionError:
            print('Missing-fields test failed')


if __name__ == '__main__':
    run()
