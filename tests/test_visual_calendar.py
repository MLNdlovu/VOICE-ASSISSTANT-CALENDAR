"""
Unit Tests for Visual Calendar Analysis

Tests for calendar visualization, heatmap generation, stress analysis,
and visual insights.
"""

import pytest
from datetime import datetime, timedelta
from src.visual_calendar import (
    VisualCalendarAnalyzer,
    CalendarHeatmap,
    TimeSlotIntensity,
    StressLevel,
    DayAnalysis,
    WeekAnalysis,
    MonthAnalysis
)


class TestTimeSlotAnalysis:
    """Test time slot analysis."""
    
    def test_empty_day_analysis(self):
        """Test analyzing an empty day."""
        analyzer = VisualCalendarAnalyzer(use_gpt=False)
        analysis = analyzer.analyze_day([], '2024-03-15')
        
        assert analysis.event_count == 0
        assert analysis.intensity == TimeSlotIntensity.FREE
        assert analysis.stress_level == StressLevel.LOW
        assert analysis.capacity_percentage == 0.0
    
    def test_light_day_analysis(self):
        """Test analyzing a light day."""
        events = [
            {'title': 'Meeting', 'start': '10:00', 'duration_minutes': 60}
        ]
        
        analyzer = VisualCalendarAnalyzer(use_gpt=False)
        analysis = analyzer.analyze_day(events, '2024-03-15')
        
        assert analysis.event_count == 1
        assert analysis.intensity == TimeSlotIntensity.LIGHT
        assert analysis.stress_level == StressLevel.LOW
    
    def test_moderate_day_analysis(self):
        """Test analyzing a moderate day."""
        events = [
            {'title': 'Meeting 1', 'start': '09:00', 'duration_minutes': 60},
            {'title': 'Meeting 2', 'start': '11:00', 'duration_minutes': 60},
            {'title': 'Meeting 3', 'start': '14:00', 'duration_minutes': 60}
        ]
        
        analyzer = VisualCalendarAnalyzer(use_gpt=False)
        analysis = analyzer.analyze_day(events, '2024-03-15')
        
        assert analysis.event_count == 3
        assert analysis.intensity == TimeSlotIntensity.MODERATE
        assert analysis.stress_level == StressLevel.MODERATE
    
    def test_busy_day_analysis(self):
        """Test analyzing a busy day."""
        events = [
            {'title': f'Meeting {i}', 'start': f'{9+i:02d}:00', 'duration_minutes': 60}
            for i in range(6)
        ]
        
        analyzer = VisualCalendarAnalyzer(use_gpt=False)
        analysis = analyzer.analyze_day(events, '2024-03-15')
        
        assert analysis.event_count == 6
        assert analysis.intensity == TimeSlotIntensity.PACKED
        assert analysis.stress_level == StressLevel.CRITICAL


class TestDayAnalysis:
    """Test day analysis data."""
    
    def test_day_analysis_creation(self):
        """Test creating day analysis."""
        analysis = DayAnalysis(
            date='2024-03-15',
            day_name='Friday',
            event_count=3,
            total_booked=180,
            total_capacity=1440,
            capacity_percentage=12.5,
            intensity=TimeSlotIntensity.LIGHT,
            stress_level=StressLevel.LOW,
            busiest_hour=10
        )
        
        assert analysis.date == '2024-03-15'
        assert analysis.day_name == 'Friday'
        assert analysis.event_count == 3
    
    def test_day_description(self):
        """Test day gets proper description."""
        analyzer = VisualCalendarAnalyzer(use_gpt=False)
        events = [{'title': 'Meeting', 'start': '10:00', 'duration_minutes': 60}]
        analysis = analyzer.analyze_day(events, '2024-03-15')
        
        assert analysis.description != ""
        assert 'Meeting' in analysis.description or 'Light' in analysis.description


class TestWeekAnalysis:
    """Test week analysis."""
    
    def test_week_analysis_creation(self):
        """Test creating week analysis."""
        day1 = DayAnalysis(
            date='2024-03-11', day_name='Monday', event_count=2,
            total_booked=120, total_capacity=1440, capacity_percentage=8.3,
            intensity=TimeSlotIntensity.LIGHT, stress_level=StressLevel.LOW, busiest_hour=10
        )
        day2 = DayAnalysis(
            date='2024-03-12', day_name='Tuesday', event_count=5,
            total_booked=300, total_capacity=1440, capacity_percentage=20.8,
            intensity=TimeSlotIntensity.MODERATE, stress_level=StressLevel.MODERATE, busiest_hour=11
        )
        
        week = WeekAnalysis(
            week_number=11,
            start_date='2024-03-11',
            end_date='2024-03-17',
            days=[day1, day2],
            average_daily_load=14.5,
            busiest_day=day2,
            freest_day=day1,
            total_free_hours=23.1
        )
        
        assert week.week_number == 11
        assert len(week.days) == 2
        assert week.busiest_day == day2


class TestMonthAnalysis:
    """Test month analysis."""
    
    def test_month_analysis_creation(self):
        """Test creating month analysis."""
        week1 = WeekAnalysis(week_number=11, start_date='2024-03-01', end_date='2024-03-07')
        week2 = WeekAnalysis(week_number=12, start_date='2024-03-08', end_date='2024-03-14')
        
        month = MonthAnalysis(
            month=3,
            year=2024,
            weeks=[week1, week2],
            average_daily_load=45.0,
            overall_stress=StressLevel.HIGH
        )
        
        assert month.month == 3
        assert month.year == 2024
        assert len(month.weeks) == 2


class TestCalendarHeatmap:
    """Test heatmap generation."""
    
    def test_heatmap_intensity_mapping(self):
        """Test intensity character mapping."""
        assert CalendarHeatmap.INTENSITY_CHARS[TimeSlotIntensity.FREE] == "░"
        assert CalendarHeatmap.INTENSITY_CHARS[TimeSlotIntensity.LIGHT] == "▒"
        assert CalendarHeatmap.INTENSITY_CHARS[TimeSlotIntensity.MODERATE] == "▓"
        assert CalendarHeatmap.INTENSITY_CHARS[TimeSlotIntensity.BUSY] == "█"
        assert CalendarHeatmap.INTENSITY_CHARS[TimeSlotIntensity.PACKED] == "██"
    
    def test_heatmap_generation(self):
        """Test generating heatmap."""
        days = [
            DayAnalysis(
                date='2024-03-11', day_name='Monday', event_count=2,
                total_booked=120, total_capacity=1440, capacity_percentage=8.3,
                intensity=TimeSlotIntensity.LIGHT, stress_level=StressLevel.LOW, busiest_hour=10
            )
        ]
        
        heatmap = CalendarHeatmap.generate_weekly_heatmap(days)
        
        assert "WEEKLY HEATMAP" in heatmap
        assert "Legend" in heatmap
        assert isinstance(heatmap, str)


class TestVisualAnalyzer:
    """Test visual analyzer."""
    
    def test_analyzer_initialization(self):
        """Test creating analyzer."""
        analyzer = VisualCalendarAnalyzer(use_gpt=False)
        assert analyzer is not None
    
    def test_find_busiest_hour(self):
        """Test finding busiest hour."""
        events = [
            {'title': 'Meeting 1', 'start': '10:00', 'duration_minutes': 60},
            {'title': 'Meeting 2', 'start': '10:30', 'duration_minutes': 60},
            {'title': 'Meeting 3', 'start': '14:00', 'duration_minutes': 60}
        ]
        
        analyzer = VisualCalendarAnalyzer(use_gpt=False)
        busiest_hour = analyzer._find_busiest_hour(events)
        
        assert busiest_hour == 10  # 10:00 has 2 events
    
    def test_find_free_slots(self):
        """Test finding free time slots."""
        events = [
            {'title': 'Meeting', 'start': '10:00', 'duration_minutes': 120},  # 10-12
            {'title': 'Lunch', 'start': '12:00', 'duration_minutes': 60}      # 12-13
        ]
        
        analyzer = VisualCalendarAnalyzer(use_gpt=False)
        free_slots = analyzer._find_free_slots(events, min_duration=120)  # 2+ hours
        
        assert len(free_slots) > 0
        # Should have free time after 13:00
        assert any(slot[0] >= 13 for slot in free_slots)
    
    def test_availability_score(self):
        """Test availability score calculation."""
        analysis = DayAnalysis(
            date='2024-03-15', day_name='Friday', event_count=1,
            total_booked=60, total_capacity=1440, capacity_percentage=4.2,
            intensity=TimeSlotIntensity.LIGHT, stress_level=StressLevel.LOW, busiest_hour=10
        )
        
        analyzer = VisualCalendarAnalyzer(use_gpt=False)
        score = analyzer.get_availability_score(analysis)
        
        assert 95 < score < 96  # Should be ~95.8
    
    def test_stress_recommendations(self):
        """Test stress level recommendations."""
        month = MonthAnalysis(
            month=3, year=2024,
            overall_stress=StressLevel.HIGH
        )
        
        analyzer = VisualCalendarAnalyzer(use_gpt=False)
        recs = analyzer.get_stress_recommendations(month)
        
        assert len(recs) > 0
        assert any('buffer' in r.lower() or 'break' in r.lower() for r in recs)


class TestVisualDescriptions:
    """Test visual description generation."""
    
    def test_describe_empty_day(self):
        """Test describing an empty day."""
        analyzer = VisualCalendarAnalyzer(use_gpt=False)
        analysis = analyzer.analyze_day([], '2024-03-15')
        description = analyzer.generate_visual_description(analysis)
        
        assert description != ""
        assert 'wide' in description.lower() or 'free' in description.lower() or 'open' in description.lower()
    
    def test_describe_busy_day(self):
        """Test describing a busy day."""
        events = [
            {'title': f'Meeting {i}', 'start': f'{9+i:02d}:00', 'duration_minutes': 60}
            for i in range(6)
        ]
        
        analyzer = VisualCalendarAnalyzer(use_gpt=False)
        analysis = analyzer.analyze_day(events, '2024-03-15')
        description = analyzer.generate_visual_description(analysis)
        
        assert description != ""
        assert 'busy' in description.lower() or 'packed' in description.lower()


class TestStressAnalysis:
    """Test stress level analysis."""
    
    def test_stress_level_low(self):
        """Test low stress identification."""
        analyzer = VisualCalendarAnalyzer(use_gpt=False)
        events = [{'title': 'One meeting', 'start': '10:00', 'duration_minutes': 60}]
        analysis = analyzer.analyze_day(events, '2024-03-15')
        
        assert analysis.stress_level == StressLevel.LOW
    
    def test_stress_level_moderate(self):
        """Test moderate stress identification."""
        analyzer = VisualCalendarAnalyzer(use_gpt=False)
        events = [
            {'title': f'Meeting {i}', 'start': f'{9+i*2:02d}:00', 'duration_minutes': 90}
            for i in range(3)
        ]
        analysis = analyzer.analyze_day(events, '2024-03-15')
        
        assert analysis.stress_level == StressLevel.MODERATE
    
    def test_stress_level_high(self):
        """Test high stress identification."""
        analyzer = VisualCalendarAnalyzer(use_gpt=False)
        events = [
            {'title': f'Meeting {i}', 'start': f'{9+i:02d}:00', 'duration_minutes': 60}
            for i in range(5)
        ]
        analysis = analyzer.analyze_day(events, '2024-03-15')
        
        assert analysis.stress_level in [StressLevel.HIGH, StressLevel.CRITICAL]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
