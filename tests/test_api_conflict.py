import json
from datetime import datetime, timedelta


def make_iso(dt):
    return dt.isoformat()


class FakeEventsList:
    def __init__(self, items):
        self._items = items

    def execute(self):
        return {'items': self._items}


class FakeEvents:
    def __init__(self, items):
        self._items = items

    def list(self, calendarId=None, timeMin=None, timeMax=None, singleEvents=None, orderBy=None):
        return FakeEventsList(self._items)

    def insert(self, calendarId=None, body=None):
        class _Exec:
            def execute(self_inner):
                return {'id': 'fake-created-1'}
        return _Exec()


class FakeService:
    def __init__(self, items):
        self._items = items

    def events(self):
        return FakeEvents(self._items)


def test_api_book_conflict_returns_409(monkeypatch):
    from web_app import app

    # Create an overlapping existing event for tomorrow 10:00-11:00
    tomorrow = datetime.now() + timedelta(days=1)
    start = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    end = start + timedelta(hours=1)

    existing_event = {
        'id': 'evt-overlap-1',
        'summary': 'Busy Meeting',
        'start': {'dateTime': start.isoformat()},
        'end': {'dateTime': end.isoformat()}
    }

    fake_service = FakeService([existing_event])

    # Monkeypatch get_calendar_service to return the fake_service
    import web_app
    monkeypatch.setattr(web_app, 'get_calendar_service', lambda access_token=None: fake_service)

    client = app.test_client()
    with client.session_transaction() as sess:
        sess['access_token'] = 't'
        sess['user_email'] = 'conflict@test'

    booking_payload = {
        'email': 'conflict@test',
        'date': start.strftime('%Y-%m-%d'),
        'time': '10:15',  # overlaps with existing 10:00-11:00
        'summary': 'Test conflict booking',
        'duration': 30
    }

    resp = client.post('/api/book', json=booking_payload)
    assert resp.status_code == 409
    j = resp.get_json()
    assert 'conflicts' in j and isinstance(j['conflicts'], list)
    assert len(j['conflicts']) >= 1
    assert 'suggestions' in j and isinstance(j['suggestions'], list)
