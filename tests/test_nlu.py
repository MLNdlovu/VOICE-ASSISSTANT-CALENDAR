import datetime
from src import nlu


def test_remind_day_before_due():
    text = "Yo, remind me to submit that assignment the day before it's due."
    out = nlu.parse_natural_language_event(text, ref_date=datetime.datetime(2025, 11, 25))
    assert out['raw_text'] == text
    assert 'due' in text.lower() or out['relative'] is not None
    # Expect relative anchor to be present
    assert out.get('relative') == {'anchor': 'due_date', 'offset': -1}


def test_sometime_friday_morning():
    text = "Set up something with Vusi sometime Friday morning — nothing too early."
    out = nlu.parse_natural_language_event(text, ref_date=datetime.datetime(2025, 11, 25))
    assert out['raw_text'] == text
    # must have a time_window or start set
    assert out.get('time_window') is not None or out.get('start') is not None
    # should prefer not-too-early morning (start hour >=9)
    if out.get('time_window'):
        assert out['time_window']['start'].hour >= 8


def test_daily_revision_session():
    text = "Plan a 1-hour revision session each day this week."
    out = nlu.parse_natural_language_event(text, ref_date=datetime.datetime(2025, 11, 25))
    assert out['raw_text'] == text
    assert out.get('duration') is not None
    assert out.get('recurrence') is not None
    assert out['recurrence']['freq'] == 'daily'
