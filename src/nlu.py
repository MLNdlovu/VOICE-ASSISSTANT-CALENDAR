import re
import datetime
from typing import Optional, Dict, Any, List

try:
    import dateparser
    from dateparser.search import search_dates
except Exception:
    dateparser = None
    search_dates = None

try:
    import parsedatetime as pdt
except Exception:
    pdt = None


def _parse_duration(text: str) -> Optional[datetime.timedelta]:
    # match durations like '1-hour', '1 hour', '90 minutes', '2 hrs'
    m = re.search(r"(\d+)\s*(?:-|)?\s*(hour|hr|hours|h)\b", text, re.I)
    if m:
        hours = int(m.group(1))
        return datetime.timedelta(hours=hours)
    m = re.search(r"(\d+)\s*(?:-|)?\s*(minute|min|minutes|m)\b", text, re.I)
    if m:
        minutes = int(m.group(1))
        return datetime.timedelta(minutes=minutes)
    return None


def _find_named_times(text: str) -> Dict[str, Any]:
    # Heuristics for vague times like 'morning', 'afternoon', 'nothing too early'
    result = {}
    if re.search(r"\bmorning\b", text, re.I):
        result['time_window'] = {'start': datetime.time(hour=8, minute=0), 'end': datetime.time(hour=11, minute=0)}
    if re.search(r"\bevening\b", text, re.I):
        result['time_window'] = {'start': datetime.time(hour=17, minute=0), 'end': datetime.time(hour=20, minute=0)}
    if re.search(r"nothing too early|not too early|nothing too early\b", text, re.I):
        # nudge earliest to 9am if morning
        tw = result.get('time_window')
        if tw:
            tw['start'] = datetime.time(hour=9, minute=0)
            result['time_window'] = tw
        else:
            result['avoid_early'] = True
    return result


def _search_dates(text: str, ref_date: Optional[datetime.datetime] = None) -> List[tuple]:
    if search_dates is None:
        return []
    settings = {'PREFER_DATES_FROM': 'future'}
    if ref_date:
        settings['RELATIVE_BASE'] = ref_date
    found = search_dates(text, settings=settings)
    return found or []


def parse_natural_language_event(text: str, ref_date: Optional[datetime.datetime] = None) -> Dict[str, Any]:
    """
    Parse messy human-calendar language into a structured event description.

    Returns a dict with keys like:
      - title: suggested short title
      - start / end: datetimes if precise
      - duration: timedelta if provided
      - recurrence: dict describing recurrence rules (e.g., daily, weekly)
      - time_window: preferred time window (start time, end time)
      - relative: for expressions like 'day before it's due' -> {'anchor':'due_date','offset':-1}
      - raw_text: original text
    """
    if ref_date is None:
        ref_date = datetime.datetime.now()

    out: Dict[str, Any] = {
        'raw_text': text,
        'title': None,
        'start': None,
        'end': None,
        'duration': None,
        'recurrence': None,
        'time_window': None,
        'relative': None,
        'candidates': []
    }

    # title heuristics: look for verbs after 'remind me to' or 'set up' or 'plan'
    m = re.search(r"remind me to\s+(.+?)(?:\.|,|$)", text, re.I)
    if m:
        out['title'] = m.group(1).strip()
    else:
        m = re.search(r"(?:set up|schedule|plan)\s+(.+?)(?:\.|,|$)", text, re.I)
        if m:
            out['title'] = m.group(1).strip()

    # duration
    dur = _parse_duration(text)
    if dur:
        out['duration'] = dur

    # recurrence
    if re.search(r"\beach day this week\b|every day this week|each day this week|daily this week", text, re.I) or re.search(r"each day this week|every day this week", text, re.I):
        # build daily recurrence for remainder of current week
        today = ref_date.date()
        # ISO: week starts Monday (isoweekday 1)
        end_of_week = today + datetime.timedelta(days=(7 - today.isoweekday()))
        out['recurrence'] = {'freq': 'daily', 'until': datetime.datetime.combine(end_of_week, datetime.time.max)}

    if re.search(r"\beach day\b|every day\b|daily\b", text, re.I) and 'recurrence' not in out:
        out['recurrence'] = {'freq': 'daily'}

    # relative anchor like "day before it's due"
    if re.search(r"day before.*due|day before it's due|day before it's due", text, re.I):
        out['relative'] = {'anchor': "due_date", 'offset': -1}

    # named times
    named = _find_named_times(text)
    if 'time_window' in named:
        out['time_window'] = named['time_window']
    if 'avoid_early' in named:
        out['avoid_early'] = True

    # try to find explicit dates/times
    found = _search_dates(text, ref_date)
    for txt, dt in found:
        out['candidates'].append({'text': txt, 'dt': dt})

    # If we found an explicit date/time, set start/end/duration accordingly
    if out['candidates']:
        # choose first candidate as primary
        cand = out['candidates'][0]
        out['start'] = cand['dt']
        if out['duration']:
            out['end'] = out['start'] + out['duration']
        # if time_window exists and start has no time, adjust to window midpoint
        if out['time_window'] and isinstance(out['start'], datetime.datetime) and out['start'].time() == datetime.time(0, 0):
            tw = out['time_window']
            midpoint_hour = (tw['start'].hour + tw['end'].hour) // 2
            out['start'] = datetime.datetime.combine(out['start'].date(), datetime.time(hour=midpoint_hour, minute=0))
            if out['duration']:
                out['end'] = out['start'] + out['duration']

    # heuristics for phrases like 'sometime Friday morning — nothing too early.'
    if re.search(r"sometime\s+([A-Za-z]+)\s+(morning|afternoon|evening)", text, re.I):
        m = re.search(r"sometime\s+([A-Za-z]+)\s+(morning|afternoon|evening)", text, re.I)
        dayname = m.group(1)
        period = m.group(2)
        # try to find next weekday matching dayname
        weekday_map = {d.lower(): i for i, d in enumerate(['monday','tuesday','wednesday','thursday','friday','saturday','sunday'])}
        key = dayname.lower()
        if key in weekday_map:
            today = ref_date.date()
            target_weekday = weekday_map[key]
            days_ahead = (target_weekday - today.weekday() + 7) % 7
            if days_ahead == 0:
                days_ahead = 7
            target_date = today + datetime.timedelta(days=days_ahead)
            # use period heuristics
            if period.lower() == 'morning':
                start_time = datetime.time(hour=9 if re.search(r"nothing too early|not too early", text, re.I) else 8)
                end_time = datetime.time(hour=11)
            elif period.lower() == 'afternoon':
                start_time = datetime.time(hour=13)
                end_time = datetime.time(hour=16)
            else:
                start_time = datetime.time(hour=17)
                end_time = datetime.time(hour=20)
            out['time_window'] = {'start': start_time, 'end': end_time}
            out['start'] = datetime.datetime.combine(target_date, start_time)
            if out['duration']:
                out['end'] = out['start'] + out['duration']

    # Fallback: if no title, use text as title
    if not out['title']:
        # strip common leading verbs
        out['title'] = text.strip()

    return out


if __name__ == '__main__':
    examples = [
        "Yo, remind me to submit that assignment the day before it's due.",
        "Set up something with Vusi sometime Friday morning — nothing too early.",
        "Plan a 1-hour revision session each day this week."
    ]
    for ex in examples:
        print('Input:', ex)
        print(parse_natural_language_event(ex))
        print('---')
