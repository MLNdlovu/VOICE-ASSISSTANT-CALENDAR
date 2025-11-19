import json
from unittest.mock import Mock
import web_app


def make_mock_service(existing_description, updated_return=None):
    service = Mock()
    events_obj = Mock()
    # Mock get().execute() to return existing event
    events_obj.get.return_value.execute.return_value = {'id': 'evt1', 'description': existing_description}
    # Mock update().execute() to return updated event
    if updated_return is None:
        updated_return = {'id': 'evt1', 'description': existing_description}
    events_obj.update.return_value.execute.return_value = updated_return
    service.events.return_value = events_obj
    return service


def test_overwrite_description(monkeypatch):
    app = web_app.app
    client = app.test_client()

    # Replace get_calendar_service to return our mock
    mock_service = make_mock_service('Old description')
    monkeypatch.setattr(web_app, 'get_calendar_service', lambda access_token=None: mock_service)

    # Set session access_token
    with client.session_transaction() as sess:
        sess['access_token'] = 'token123'

    res = client.patch('/api/events/evt1/description', json={'description': 'New content', 'mode': 'overwrite'})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data.get('success') is True

    # Check update called with overwritten description
    called_body = mock_service.events.return_value.update.call_args[1]['body']
    assert called_body['description'] == 'New content'


def test_append_description(monkeypatch):
    app = web_app.app
    client = app.test_client()

    mock_service = make_mock_service('Existing notes')
    monkeypatch.setattr(web_app, 'get_calendar_service', lambda access_token=None: mock_service)

    with client.session_transaction() as sess:
        sess['access_token'] = 'token123'

    res = client.patch('/api/events/evt1/description', json={'description': 'Appended text', 'mode': 'append'})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data.get('success') is True

    called_body = mock_service.events.return_value.update.call_args[1]['body']
    expected = 'Existing notes\n\n---\n\nAppended text'
    assert called_body['description'] == expected
