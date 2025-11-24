"""
Lightweight event recommender for Voice Assistant Calendar.

This module analyzes past calendar events and suggests bookings the user
commonly creates. It uses simple heuristics (frequency, common weekday/time)
so it works without heavy ML dependencies. Optionally a scikit-learn model
can be added later for advanced suggestions.

Functions:
- analyze_events_for_recommendations(service, lookback_days=90, max_items=5)

Returns a list of suggestion dicts with fields: summary, count, weekday,
common_time, suggested_slots (ISO datetimes) for the next few occurrences.

"""
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import List, Dict

try:
    from dateutil import parser as date_parser
    DATEUTIL_AVAILABLE = True
except Exception:
    DATEUTIL_AVAILABLE = False


def _next_weekday_occurrence(start_dt: datetime, target_weekday: int) -> datetime:
    """Return the next datetime (>= start_dt) that has weekday target_weekday."""
    days_ahead = (target_weekday - start_dt.weekday()) % 7
    candidate = start_dt + timedelta(days=days_ahead)
    return candidate


def analyze_events_for_recommendations(service, lookback_days: int = 90, max_items: int = 5) -> List[Dict]:
    """Analyze past events from `service` and return recommendations.

    - Fetches events from (now - lookback_days) to now.
    - Groups by summary (normalized), computes counts and common time/weekday.
    - Returns top `max_items` suggestions with suggested next slots.
    """
    if service is None:
        return []

    now = datetime.now(timezone.utc)
    time_min = (now - timedelta(days=lookback_days)).isoformat()

    try:
        events_result = (
            service.events()
            .list(calendarId='primary', timeMin=time_min, maxResults=2500, singleEvents=True, orderBy='startTime')
            .execute()
        )
        events = events_result.get('items', [])
    except Exception:
        events = []

    # Aggregate stats by normalized summary
    summary_counts = Counter()
    times_by_summary = defaultdict(list)  # list of (hour, minute)
    weekdays_by_summary = defaultdict(list)  # list of weekday ints

    for ev in events:
        summary = ev.get('summary')
        if not summary:
            continue
        norm = summary.strip().lower()

        # parse start datetime
        start = ev.get('start', {})
        start_dt = None
        dt_str = start.get('dateTime') or start.get('date')
        if not dt_str:
            continue
        try:
            if DATEUTIL_AVAILABLE:
                start_dt = date_parser.parse(dt_str)
            else:
                # attempt ISO parse
                start_dt = datetime.fromisoformat(dt_str)
        except Exception:
            continue

        summary_counts[norm] += 1
        times_by_summary[norm].append((start_dt.hour, start_dt.minute))
        weekdays_by_summary[norm].append(start_dt.weekday())

    # Build recommendations
    recommendations = []
    for norm, count in summary_counts.most_common(max_items):
        # choose most common time
        time_counter = Counter(times_by_summary[norm])
        (hour, minute), _ = time_counter.most_common(1)[0]

        weekday_counter = Counter(weekdays_by_summary[norm])
        weekday_most, _ = weekday_counter.most_common(1)[0]

        # propose next 3 occurrences for that weekday and time
        suggested_slots = []
        base = datetime.now()
        for i in range(1, 8):
            candidate_day = base + timedelta(days=i)
            # find next occurrence of the weekday at or after today
            next_occ = _next_weekday_occurrence(base + timedelta(days=i-1), weekday_most)
            # set time
            try:
                candidate_dt = datetime(year=next_occ.year, month=next_occ.month, day=next_occ.day, hour=hour, minute=minute)
                # naive local time; convert to isoformat without timezone to keep consistent with client
                suggested_slots.append(candidate_dt.isoformat())
            except Exception:
                continue
            if len(suggested_slots) >= 3:
                break

        recommendations.append({
            'summary': norm.title(),
            'count': count,
            'common_time': f"{hour:02d}:{minute:02d}",
            'weekday': ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][weekday_most],
            'suggested_slots': suggested_slots
        })

    return recommendations


# Simple wrapper to be used by the web app; keeps API small and testable
def get_recommendations_for_service(service, lookback_days: int = 90, max_items: int = 5):
    try:
        return analyze_events_for_recommendations(service, lookback_days=lookback_days, max_items=max_items)
    except Exception:
        return []
