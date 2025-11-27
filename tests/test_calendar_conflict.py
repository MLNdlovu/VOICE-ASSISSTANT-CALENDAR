import pytest
from datetime import datetime, timedelta
from src.calendar_conflict import ConflictDetector, TimeSlot


def test_detect_conflict_and_suggest():
    detector = ConflictDetector(timezone='Africa/Johannesburg')

    # Proposed meeting tomorrow 10:00 - 10:30 (make tz-aware)
    tomorrow = datetime.now() + timedelta(days=1)
    naive_start = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    proposed_start = detector.timezone.localize(naive_start)
    proposed_end = proposed_start + timedelta(minutes=30)
    proposed = TimeSlot(proposed_start, proposed_end)

    # Existing event overlaps (10:15 - 11:00)
    existing_start = proposed_start + timedelta(minutes=15)
    existing_end = existing_start + timedelta(minutes=45)
    existing_events = [
        {
            'id': 'evt1',
            'summary': 'Existing Meeting',
            'start': {'dateTime': existing_start.isoformat()},
            'end': {'dateTime': existing_end.isoformat()}
        }
    ]

    conflicts = detector.detect_conflicts(proposed, existing_events)
    assert len(conflicts) == 1
    assert conflicts[0]['event_title'] == 'Existing Meeting'

    # Suggest alternatives (should return at least one free slot)
    suggestions = detector.suggest_alternatives(proposed, existing_events, duration_minutes=30, max_suggestions=3, search_days=2)
    assert isinstance(suggestions, list)
    assert len(suggestions) > 0

    # Resolution suggestion
    resolution = detector.resolve_conflict(proposed, conflicts, resolution_type='move')
    assert resolution['action'] == 'move'
    assert resolution['type'] == 'need_alternatives'


def test_availability_summary_no_events():
    detector = ConflictDetector()
    date_str = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
    # Provide timezone string to avoid double-wrapping timezone object
    summary = detector.get_availability_summary([], date_str, timezone='Africa/Johannesburg')
    assert summary['date'] == date_str
    assert summary['total_events'] == 0
    assert 'free_slots' in summary
    assert summary['is_fully_booked'] == False
