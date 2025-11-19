import json
from unittest.mock import Mock
import web_app


def make_mock_bot(response_text):
    bot = Mock()
    bot.chat.return_value = response_text
    return bot


def setup_client_with_token(client):
    with client.session_transaction() as sess:
        sess['access_token'] = 'token123'


def test_ai_actions_endpoint(monkeypatch):
    app = web_app.app
    client = app.test_client()
    setup_client_with_token(client)

    mock_bot = make_mock_bot('1. Do X\n2. Do Y')
    monkeypatch.setattr(web_app, 'get_chatbot', lambda: mock_bot)

    res = client.post('/api/ai/actions', json={'title': 'Team Sync', 'notes': 'Discuss project; John to follow up'})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data.get('success') is True
    assert 'actions' in data


def test_ai_email_endpoint(monkeypatch):
    app = web_app.app
    client = app.test_client()
    setup_client_with_token(client)

    mock_bot = make_mock_bot('Subject: Follow-up\nBody: Thanks everyone...')
    monkeypatch.setattr(web_app, 'get_chatbot', lambda: mock_bot)

    res = client.post('/api/ai/email', json={'title': 'Project Update', 'recipients': ['a@example.com'], 'context': 'Summary of meeting'})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data.get('success') is True
    assert 'email' in data


def test_ai_suggest_times_endpoint(monkeypatch):
    app = web_app.app
    client = app.test_client()
    setup_client_with_token(client)

    mock_bot = make_mock_bot('2025-11-20T10:00, 2025-11-20T14:00, 2025-11-21T09:00')
    monkeypatch.setattr(web_app, 'get_chatbot', lambda: mock_bot)

    res = client.post('/api/ai/suggest-times', json={'duration': 30, 'participants': ['a@example.com']})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data.get('success') is True
    assert 'suggestions' in data
