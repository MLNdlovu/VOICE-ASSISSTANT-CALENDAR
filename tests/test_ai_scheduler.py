"""
Unit tests for AI Smart Scheduler module
"""

import datetime
import pytest
from src.ai_scheduler import (
    TimeSlot,
    SchedulePreferences,
    AvailabilityBuilder,
    SmartScheduler
)


class TestTimeSlot:
    def test_timeslot_creation(self):
        start = datetime.datetime(2025, 11, 25, 9, 0)
        end = datetime.datetime(2025, 11, 25, 11, 0)
        slot = TimeSlot(start=start, end=end, duration_minutes=120)
        
        assert slot.start == start
        assert slot.end == end
        assert slot.duration_minutes == 120

    def test_timeslot_to_dict(self):
        start = datetime.datetime(2025, 11, 25, 9, 0)
        end = datetime.datetime(2025, 11, 25, 10, 0)
        slot = TimeSlot(start=start, end=end, duration_minutes=60, reason="available")
        
        d = slot.to_dict()
        assert 'start' in d
        assert 'end' in d
        assert d['duration_minutes'] == 60


class TestSchedulePreferences:
    def test_default_preferences(self):
        prefs = SchedulePreferences()
        assert prefs.work_hours_only is True
        assert prefs.earliest_hour == 9
        assert prefs.latest_hour == 17

    def test_custom_preferences(self):
        prefs = SchedulePreferences(
            avoid_times=['morning', 'weekend'],
            preferred_times=['afternoon'],
            earliest_hour=10,
            latest_hour=18
        )
        assert 'morning' in prefs.avoid_times
        assert 'afternoon' in prefs.preferred_times
        assert prefs.earliest_hour == 10


class TestAvailabilityBuilder:
    def test_no_events_returns_full_range(self):
        prefs = SchedulePreferences(work_hours_only=False)
        builder = AvailabilityBuilder(prefs)
        
        start = datetime.datetime(2025, 11, 25, 8, 0)
        end = datetime.datetime(2025, 11, 25, 17, 0)
        
        slots = builder.build_availability_blocks([], start, end, duration_minutes=60)
        
        assert len(slots) > 0
        assert slots[0].start == start

    def test_single_busy_event_creates_gaps(self):
        prefs = SchedulePreferences(work_hours_only=False)
        builder = AvailabilityBuilder(prefs)
        
        start = datetime.datetime(2025, 11, 25, 8, 0)
        end = datetime.datetime(2025, 11, 25, 18, 0)
        
        # Event from 12-13
        events = [
            {
                'start': {'dateTime': '2025-11-25T12:00:00'},
                'end': {'dateTime': '2025-11-25T13:00:00'}
            }
        ]
        
        slots = builder.build_availability_blocks(events, start, end, duration_minutes=60)
        
        # Should have gaps before and after the event
        assert len(slots) >= 1

    def test_preferences_filtering_morning(self):
        prefs = SchedulePreferences(avoid_times=['morning'])
        builder = AvailabilityBuilder(prefs)
        
        start = datetime.datetime(2025, 11, 25, 8, 0)
        end = datetime.datetime(2025, 11, 25, 18, 0)
        
        slots = builder.build_availability_blocks([], start, end, duration_minutes=60)
        
        # Morning hours should be filtered out
        for slot in slots:
            assert slot.start.hour >= 12 or slot.start.hour < 8

    def test_preferences_filtering_weekend(self):
        prefs = SchedulePreferences(avoid_times=['weekend'])
        builder = AvailabilityBuilder(prefs)
        
        # Saturday 2025-11-29
        start = datetime.datetime(2025, 11, 29, 9, 0)
        end = datetime.datetime(2025, 11, 29, 17, 0)
        
        slots = builder.build_availability_blocks([], start, end, duration_minutes=60)
        
        # No slots on weekend
        assert len(slots) == 0

    def test_work_hours_filtering(self):
        prefs = SchedulePreferences(work_hours_only=True, earliest_hour=9, latest_hour=17)
        builder = AvailabilityBuilder(prefs)
        
        # Tuesday 2025-11-25 (weekday)
        start = datetime.datetime(2025, 11, 25, 7, 0)
        end = datetime.datetime(2025, 11, 25, 19, 0)
        
        slots = builder.build_availability_blocks([], start, end, duration_minutes=60)
        
        # Should only have slots within 9-17
        for slot in slots:
            assert 9 <= slot.start.hour < 17


class TestSmartScheduler:
    def test_scheduler_initialization(self):
        prefs = SchedulePreferences()
        scheduler = SmartScheduler(preferences=prefs)
        
        assert scheduler.preferences == prefs

    def test_find_best_times_no_events(self):
        prefs = SchedulePreferences(work_hours_only=False)
        scheduler = SmartScheduler(preferences=prefs)
        
        start = datetime.datetime(2025, 11, 25, 9, 0)
        results = scheduler.find_best_times(
            event_description="2-hour meeting",
            duration_minutes=120,
            search_window_days=1,
            top_n=3,
            start_date=start
        )
        
        assert results['status'] == 'success'
        assert 'recommendations' in results
        assert results['duration_minutes'] == 120

    def test_find_best_times_insufficient_slots(self):
        prefs = SchedulePreferences(work_hours_only=False)
        scheduler = SmartScheduler(preferences=prefs)
        
        # Very limited window (1 hour)
        start = datetime.datetime(2025, 11, 25, 9, 0)
        results = scheduler.find_best_times(
            event_description="8-hour marathon",
            duration_minutes=480,
            search_window_days=1,
            top_n=3,
            start_date=start
        )
        
        # May not find slots given the constraint
        assert 'status' in results
