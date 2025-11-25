"""
AI Agenda Summary Module

Generates natural, human-friendly summaries of calendar events.
Supports daily, weekly, and custom time range summaries.

Examples:
- "You've got a chilled Monday: one study session at 10, then a 3PM meeting. Nothing urgent."
- "Your week is packed: 12 meetings scheduled, mostly afternoons. Wednesday is your busiest day with 4 back-to-back sessions."
- "Pretty light schedule today - just one 30-minute call at 2pm."
"""

import datetime
from typing import List, Dict, Any, Optional, Tuple
import os
from dataclasses import dataclass

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


@dataclass
class AgendaEvent:
    """Represents a calendar event for summary purposes."""
    title: str
    start: datetime.datetime
    end: datetime.datetime
    duration_minutes: int
    is_busy: bool = True
    description: str = ""

    def format_time(self) -> str:
        """Format as 'HH:MM' or '3:30 PM'."""
        return self.start.strftime('%I:%M %p').lstrip('0')

    def is_all_day(self) -> bool:
        """Check if event is all-day."""
        return self.duration_minutes >= 1440

    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'start': self.start.isoformat(),
            'end': self.end.isoformat(),
            'duration_minutes': self.duration_minutes,
            'is_busy': self.is_busy,
            'description': self.description
        }


class EventAnalyzer:
    """Analyzes calendar events for summary generation."""

    def __init__(self):
        pass

    @staticmethod
    def categorize_event(title: str, description: str = "") -> str:
        """Categorize event type."""
        combined = (title + " " + description).lower()
        
        keywords = {
            'meeting': ['meeting', 'sync', 'standup', 'huddle', 'conference'],
            'class': ['class', 'lecture', 'course', 'training', 'workshop'],
            'focus': ['focus', 'deep work', 'development', 'coding', 'writing', 'review'],
            'call': ['call', 'zoom', 'teams', 'video'],
            'break': ['break', 'lunch', 'coffee', 'break time', 'rest'],
            'social': ['lunch', 'dinner', 'drinks', 'hangout', 'catch', 'friend', 'date'],
            'admin': ['admin', 'paperwork', 'inbox', 'email', 'docs'],
        }
        
        for category, keywords_list in keywords.items():
            if any(kw in combined for kw in keywords_list):
                return category
        
        return 'event'

    @staticmethod
    def is_busy_time(hour: int) -> str:
        """Categorize time of day."""
        if 0 <= hour < 8:
            return 'early_morning'
        elif 8 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 14:
            return 'midday'
        elif 14 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 20:
            return 'evening'
        else:
            return 'night'

    @staticmethod
    def group_events_by_day(events: List[AgendaEvent]) -> Dict[datetime.date, List[AgendaEvent]]:
        """Group events by date."""
        grouped = {}
        for event in events:
            date = event.start.date()
            if date not in grouped:
                grouped[date] = []
            grouped[date].append(event)
        
        # Sort events within each day by time
        for date in grouped:
            grouped[date].sort(key=lambda e: e.start)
        
        return grouped

    @staticmethod
    def calculate_day_metrics(events: List[AgendaEvent]) -> Dict[str, Any]:
        """Calculate metrics for a single day."""
        if not events:
            return {
                'total_events': 0,
                'busy_minutes': 0,
                'free_minutes': 1440,
                'busiest_hour': None,
                'has_conflicts': False
            }

        # Sort by start time
        events = sorted(events, key=lambda e: e.start)
        
        total_busy_minutes = sum(e.duration_minutes for e in events)
        first_event = events[0]
        last_event = events[-1]
        
        # Check for overlaps
        has_conflicts = False
        for i in range(len(events) - 1):
            if events[i].end > events[i + 1].start:
                has_conflicts = True
                break

        # Find busiest hour
        hour_counts = {}
        for event in events:
            start_hour = event.start.hour
            hour_counts[start_hour] = hour_counts.get(start_hour, 0) + 1
        
        busiest_hour = max(hour_counts, key=hour_counts.get) if hour_counts else None

        return {
            'total_events': len(events),
            'busy_minutes': total_busy_minutes,
            'free_minutes': 1440 - total_busy_minutes,
            'first_event_time': first_event.start,
            'last_event_time': last_event.end,
            'busiest_hour': busiest_hour,
            'has_conflicts': has_conflicts,
            'event_types': [EventAnalyzer.categorize_event(e.title, e.description) for e in events]
        }

    @staticmethod
    def calculate_week_metrics(events: List[AgendaEvent]) -> Dict[str, Any]:
        """Calculate metrics for a week."""
        if not events:
            return {
                'total_events': 0,
                'total_busy_hours': 0,
                'days_with_events': 0,
                'busiest_day': None,
                'lightest_day': None
            }

        grouped = EventAnalyzer.group_events_by_day(events)
        day_metrics = {date: EventAnalyzer.calculate_day_metrics(day_events) 
                      for date, day_events in grouped.items()}
        
        busiest_day = max(day_metrics.items(), key=lambda x: x[1]['busy_minutes'])[0]
        lightest_day = min(day_metrics.items(), key=lambda x: x[1]['busy_minutes'])[0]
        
        return {
            'total_events': len(events),
            'total_busy_hours': sum(m['busy_minutes'] for m in day_metrics.values()) / 60,
            'days_with_events': len(grouped),
            'busiest_day': busiest_day,
            'lightest_day': lightest_day,
            'day_metrics': day_metrics,
            'avg_events_per_day': len(events) / len(grouped) if grouped else 0
        }


class AgendaSummaryGenerator:
    """Generates natural language summaries from events."""

    def __init__(self):
        self.analyzer = EventAnalyzer()

    def generate_day_summary(self, events: List[AgendaEvent], target_date: Optional[datetime.date] = None) -> str:
        """
        Generate a natural summary for a single day.
        
        Args:
            events: List of events on that day
            target_date: Date to summarize (for context)
        
        Returns:
            Natural language summary
        """
        if target_date is None:
            target_date = datetime.datetime.now().date()

        if not events:
            day_name = target_date.strftime('%A')
            return f"You've got a wide open {day_name} - no meetings scheduled!"

        # Calculate metrics
        metrics = self.analyzer.calculate_day_metrics(events)
        events = sorted(events, key=lambda e: e.start)

        # Build natural summary
        day_name = target_date.strftime('%A')
        free_hours = metrics['free_minutes'] / 60
        event_count = metrics['total_events']

        # Opening phrase based on busyness
        if metrics['busy_minutes'] < 120:
            opening = f"Pretty light schedule today - "
            tone = "relaxed"
        elif metrics['busy_minutes'] < 360:
            opening = f"You've got a chilled {day_name}: "
            tone = "casual"
        elif metrics['busy_minutes'] < 540:
            opening = f"Moderately busy {day_name}: "
            tone = "neutral"
        else:
            opening = f"Packed {day_name}: "
            tone = "busy"

        # Event listing
        if event_count == 1:
            event = events[0]
            event_str = f"one {self.analyzer.categorize_event(event.title)} at {event.format_time()}"
        elif event_count == 2:
            times = " and ".join(e.format_time() for e in events[:2])
            event_str = f"two events at {times}"
        else:
            # Group by time periods
            morning = [e for e in events if 5 <= e.start.hour < 12]
            afternoon = [e for e in events if 12 <= e.start.hour < 17]
            evening = [e for e in events if 17 <= e.start.hour < 24]

            parts = []
            if morning:
                parts.append(f"{len(morning)} in the morning")
            if afternoon:
                parts.append(f"{len(afternoon)} in the afternoon")
            if evening:
                parts.append(f"{len(evening)} in the evening")

            event_str = f"{event_count} events: " + ", ".join(parts)

        # Urgency check
        urgency = ""
        if metrics['has_conflicts']:
            urgency = " Note: you have overlapping events!"
        elif free_hours >= 4:
            urgency = " Plenty of free time."
        elif free_hours >= 2:
            urgency = " Some breaks available."

        return opening + event_str + urgency.rstrip(".")

    def generate_week_summary(self, events: List[AgendaEvent], start_date: Optional[datetime.date] = None) -> str:
        """
        Generate a natural summary for a week.
        
        Args:
            events: List of events in the week
            start_date: Start of week (for context)
        
        Returns:
            Natural language summary
        """
        if start_date is None:
            start_date = datetime.datetime.now().date()

        if not events:
            return "Your week is completely clear - no meetings scheduled!"

        metrics = self.analyzer.calculate_week_metrics(events)
        event_count = metrics['total_events']
        busy_hours = metrics['total_busy_hours']
        avg_per_day = metrics['avg_events_per_day']

        # Opening based on workload
        if event_count <= 5:
            opening = f"Light week ahead: {event_count} events total. "
        elif event_count <= 15:
            opening = f"Moderately busy week: {event_count} meetings scheduled. "
        else:
            opening = f"Your week is packed: {event_count} meetings on the calendar. "

        # Distribution info
        if metrics['days_with_events'] <= 2:
            distribution = f"Everything's concentrated in {metrics['days_with_events']} days."
        elif metrics['days_with_events'] <= 4:
            distribution = f"Spread across {metrics['days_with_events']} days."
        else:
            distribution = f"Spread across all {metrics['days_with_events']} days of the week."

        # Busiest day callout
        busiest = metrics['busiest_day']
        busiest_day_name = busiest.strftime('%A') if busiest else ""
        lightest = metrics['lightest_day']
        lightest_day_name = lightest.strftime('%A') if lightest else ""

        detail = f"{distribution} "
        if busiest:
            busiest_metrics = metrics['day_metrics'][busiest]
            detail += f"{busiest_day_name} is your busiest day with {busiest_metrics['total_events']} events. "
        if lightest and lightest != busiest:
            detail += f"{lightest_day_name} is lighter."

        return opening + detail.rstrip()

    def generate_custom_range_summary(self, events: List[AgendaEvent], start_date: datetime.date, end_date: datetime.date) -> str:
        """Generate summary for custom date range."""
        days = (end_date - start_date).days + 1
        
        if not events:
            if days == 1:
                return f"No events scheduled for {start_date.strftime('%A, %B %d')}."
            else:
                return f"No events scheduled from {start_date} to {end_date}."

        grouped = self.analyzer.group_events_by_day(events)
        
        if days <= 7:
            return self.generate_week_summary(events, start_date)
        else:
            # Month-like summary
            return f"You have {len(events)} events scheduled across {len(grouped)} days in this period."


class GPTAgendaSummarizer:
    """Uses GPT to enhance and customize agenda summaries."""

    def __init__(self, api_key: Optional[str] = None):
        if not HAS_OPENAI:
            raise ImportError("OpenAI not installed")
        
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key

    def enhance_summary(self, base_summary: str, tone: str = "friendly", include_priorities: bool = False) -> str:
        """
        Use GPT to enhance and personalize a summary.
        
        Args:
            base_summary: Base summary from AgendaSummaryGenerator
            tone: 'friendly', 'professional', 'casual', 'brief'
            include_priorities: Whether to suggest priorities
        
        Returns:
            Enhanced summary
        """
        if not HAS_OPENAI:
            return base_summary

        prompt = f"""You are a friendly AI calendar assistant. 
Enhance this calendar summary to be more engaging and in a {tone} tone.
Keep it concise (1-2 sentences) and conversational.
{f"Include what priorities you suggest for the user." if include_priorities else ""}

Original summary: "{base_summary}"

Enhanced summary:"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )
            return response['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"Error enhancing summary with GPT: {e}")
            return base_summary

    def add_insights(self, summary: str, events: List[AgendaEvent], focus_area: str = "balance") -> str:
        """
        Add actionable insights using GPT.
        
        Args:
            summary: Base summary
            events: Event list for context
            focus_area: 'balance', 'productivity', 'wellbeing', 'teamwork'
        
        Returns:
            Summary with insights
        """
        if not events or not HAS_OPENAI:
            return summary

        event_titles = ", ".join([e.title for e in events[:5]])
        
        prompt = f"""Based on this calendar summary and events, provide ONE brief insight focused on {focus_area}.
Keep it to 1 sentence, actionable and encouraging.

Summary: {summary}
Events: {event_titles}

Insight:"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=80,
                temperature=0.7
            )
            insight = response['choices'][0]['message']['content'].strip()
            return f"{summary} {insight}"
        except Exception as e:
            return summary


class AgendaSummaryService:
    """Main service for agenda summaries."""

    def __init__(self, use_gpt: bool = True):
        self.generator = AgendaSummaryGenerator()
        self.gpt_summarizer = None
        
        if use_gpt and HAS_OPENAI:
            try:
                self.gpt_summarizer = GPTAgendaSummarizer()
            except Exception as e:
                print(f"[WARN] GPT summarizer not available: {e}")

    def get_today_summary(self, events: List[AgendaEvent], use_gpt: bool = False) -> str:
        """Get summary for today."""
        summary = self.generator.generate_day_summary(events)
        
        if use_gpt and self.gpt_summarizer:
            summary = self.gpt_summarizer.enhance_summary(summary, tone="friendly")
        
        return summary

    def get_week_summary(self, events: List[AgendaEvent], use_gpt: bool = False) -> str:
        """Get summary for current week."""
        summary = self.generator.generate_week_summary(events)
        
        if use_gpt and self.gpt_summarizer:
            summary = self.gpt_summarizer.enhance_summary(summary, tone="professional")
        
        return summary

    def get_custom_summary(self, events: List[AgendaEvent], start_date: datetime.date, end_date: datetime.date) -> str:
        """Get summary for custom date range."""
        return self.generator.generate_custom_range_summary(events, start_date, end_date)

    def get_summary_with_details(self, events: List[AgendaEvent], period: str = "day") -> Dict[str, Any]:
        """Get summary plus detailed metrics."""
        if period == "day":
            summary = self.get_today_summary(events)
            metrics = self.generator.analyzer.calculate_day_metrics(events) if events else {}
        else:  # week
            summary = self.get_week_summary(events)
            metrics = self.generator.analyzer.calculate_week_metrics(events) if events else {}

        return {
            'summary': summary,
            'metrics': metrics,
            'event_count': len(events),
            'period': period
        }


if __name__ == '__main__':
    # Example usage
    import datetime as dt
    
    # Mock events
    today = dt.datetime.now()
    events = [
        AgendaEvent("Study session", today.replace(hour=10, minute=0), 
                   today.replace(hour=11, minute=0), 60),
        AgendaEvent("Team meeting", today.replace(hour=15, minute=0),
                   today.replace(hour=16, minute=0), 60),
    ]
    
    service = AgendaSummaryService(use_gpt=False)
    
    print("Today's summary:")
    print(service.get_today_summary(events))
    
    print("\nWith details:")
    print(service.get_summary_with_details(events, period="day"))
