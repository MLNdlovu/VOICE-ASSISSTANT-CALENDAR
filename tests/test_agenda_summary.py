"""
Unit tests for Agenda Summary Module
"""

import datetime
import pytest
from src.agenda_summary import (
    AgendaEvent,
    EventAnalyzer,
    AgendaSummaryGenerator
)


class TestAgendaEvent:
    def test_agenda_event_creation(self):
        start = datetime.datetime(2025, 11, 25, 10, 0)
        end = datetime.datetime(2025, 11, 25, 11, 0)
        event = AgendaEvent("Meeting", start, end, 60)
        
        assert event.title == "Meeting"
        assert event.duration_minutes == 60

    def test_format_time(self):
        start = datetime.datetime(2025, 11, 25, 14, 30)
        end = datetime.datetime(2025, 11, 25, 15, 30)
        event = AgendaEvent("Test", start, end, 60)
        
        formatted = event.format_time()
        assert "2:30" in formatted or "14:30" in formatted or "2:30 PM" in formatted

    def test_is_all_day(self):
        start = datetime.datetime(2025, 11, 25, 0, 0)
        end = datetime.datetime(2025, 11, 26, 0, 0)
        event = AgendaEvent("All Day", start, end, 1440)
        
        assert event.is_all_day() is True


class TestEventAnalyzer:
    def test_categorize_event(self):
        # Meeting
        assert EventAnalyzer.categorize_event("Team Standup") == 'meeting'
        
        # Class
        assert EventAnalyzer.categorize_event("Python Course") == 'class'
        
        # Call
        assert EventAnalyzer.categorize_event("Zoom call") == 'call'

    def test_is_busy_time(self):
        assert EventAnalyzer.is_busy_time(7) == 'early_morning'
        assert EventAnalyzer.is_busy_time(10) == 'morning'
        assert EventAnalyzer.is_busy_time(13) == 'midday'
        assert EventAnalyzer.is_busy_time(15) == 'afternoon'
        assert EventAnalyzer.is_busy_time(18) == 'evening'
        assert EventAnalyzer.is_busy_time(22) == 'night'

    def test_group_events_by_day(self):
        today = datetime.datetime.now()
        tomorrow = today + datetime.timedelta(days=1)
        
        events = [
            AgendaEvent("Event 1", today.replace(hour=10), today.replace(hour=11), 60),
            AgendaEvent("Event 2", today.replace(hour=14), today.replace(hour=15), 60),
            AgendaEvent("Event 3", tomorrow.replace(hour=10), tomorrow.replace(hour=11), 60),
        ]
        
        grouped = EventAnalyzer.group_events_by_day(events)
        
        assert len(grouped) == 2
        assert today.date() in grouped
        assert tomorrow.date() in grouped

    def test_calculate_day_metrics_empty(self):
        metrics = EventAnalyzer.calculate_day_metrics([])
        
        assert metrics['total_events'] == 0
        assert metrics['busy_minutes'] == 0
        assert metrics['free_minutes'] == 1440

    def test_calculate_day_metrics_with_events(self):
        today = datetime.datetime.now()
        events = [
            AgendaEvent("Event 1", today.replace(hour=9), today.replace(hour=10), 60),
            AgendaEvent("Event 2", today.replace(hour=14), today.replace(hour=15), 60),
        ]
        
        metrics = EventAnalyzer.calculate_day_metrics(events)
        
        assert metrics['total_events'] == 2
        assert metrics['busy_minutes'] == 120
        assert metrics['free_minutes'] == 1320

    def test_calculate_week_metrics(self):
        today = datetime.datetime.now()
        events = [
            AgendaEvent("Event 1", today.replace(hour=10), today.replace(hour=11), 60),
            AgendaEvent("Event 2", today.replace(day=today.day+1, hour=14), 
                       today.replace(day=today.day+1, hour=15), 60),
        ]
        
        metrics = EventAnalyzer.calculate_week_metrics(events)
        
        assert metrics['total_events'] == 2
        assert metrics['days_with_events'] == 2


class TestAgendaSummaryGenerator:
    def test_generator_creation(self):
        gen = AgendaSummaryGenerator()
        assert gen.analyzer is not None

    def test_generate_day_summary_empty(self):
        gen = AgendaSummaryGenerator()
        summary = gen.generate_day_summary([])
        
        assert "wide open" in summary or "no meetings" in summary

    def test_generate_day_summary_light(self):
        gen = AgendaSummaryGenerator()
        today = datetime.datetime.now()
        events = [
            AgendaEvent("Study", today.replace(hour=10), today.replace(hour=11), 60),
        ]
        
        summary = gen.generate_day_summary(events)
        
        assert len(summary) > 0
        assert "light" in summary or "one" in summary

    def test_generate_day_summary_busy(self):
        gen = AgendaSummaryGenerator()
        today = datetime.datetime.now()
        events = [
            AgendaEvent("Meeting 1", today.replace(hour=9), today.replace(hour=10), 60),
            AgendaEvent("Meeting 2", today.replace(hour=10), today.replace(hour=11), 60),
            AgendaEvent("Meeting 3", today.replace(hour=11), today.replace(hour=12), 60),
            AgendaEvent("Meeting 4", today.replace(hour=13), today.replace(hour=14), 60),
            AgendaEvent("Meeting 5", today.replace(hour=14), today.replace(hour=15), 60),
        ]
        
        summary = gen.generate_day_summary(events)
        
        assert len(summary) > 0
        assert "packed" in summary or "5 events" in summary

    def test_generate_week_summary_empty(self):
        gen = AgendaSummaryGenerator()
        summary = gen.generate_week_summary([])
        
        assert "clear" in summary or "no meetings" in summary

    def test_generate_week_summary_light(self):
        gen = AgendaSummaryGenerator()
        today = datetime.datetime.now()
        events = [
            AgendaEvent("Event 1", today.replace(hour=10), today.replace(hour=11), 60),
        ]
        
        summary = gen.generate_week_summary(events, start_date=today.date())
        
        assert "light" in summary or "1 event" in summary

    def test_generate_week_summary_packed(self):
        gen = AgendaSummaryGenerator()
        today = datetime.datetime.now()
        events = []
        for i in range(20):
            day_offset = i // 4
            hour = 9 + (i % 4) * 2
            event_date = today + datetime.timedelta(days=day_offset)
            events.append(
                AgendaEvent(f"Meeting {i+1}", event_date.replace(hour=hour),
                           event_date.replace(hour=hour+1), 60)
            )
        
        summary = gen.generate_week_summary(events, start_date=today.date())
        
        assert len(summary) > 0
        assert ("packed" in summary or "20 meetings" in summary)

    def test_generate_custom_range_summary(self):
        gen = AgendaSummaryGenerator()
        today = datetime.datetime.now()
        tomorrow = today + datetime.timedelta(days=1)
        
        events = [
            AgendaEvent("Event 1", today.replace(hour=10), today.replace(hour=11), 60),
        ]
        
        summary = gen.generate_custom_range_summary(events, today.date(), tomorrow.date())
        
        assert len(summary) > 0
