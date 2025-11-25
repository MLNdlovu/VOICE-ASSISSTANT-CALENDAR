"""
Unit Tests for AI Patterns & Predictions Module

Tests pattern detection, prediction generation, and action planning.
"""

import pytest
from datetime import datetime, timedelta
from src.ai_patterns import (
    BusyTimeAnalyzer, EventProximityAnalyzer, ReminderPatternAnalyzer,
    FocusTimeAnalyzer, BreakPatternAnalyzer, AIInsightGenerator,
    PatternPredictionService, Pattern, Prediction, TimeBlock
)


# ============================================================================
# Test Data Fixtures
# ============================================================================

def get_sample_events():
    """Get sample calendar events for testing."""
    now = datetime.now()
    return [
        # Tuesday morning (consistent busy pattern)
        {
            'title': 'Morning Standup',
            'start_time': (now + timedelta(days=2)).replace(hour=9, minute=0).isoformat() + 'Z',
            'end_time': (now + timedelta(days=2)).replace(hour=9, minute=30).isoformat() + 'Z'
        },
        {
            'title': 'Team Sync',
            'start_time': (now + timedelta(days=2)).replace(hour=10, minute=0).isoformat() + 'Z',
            'end_time': (now + timedelta(days=2)).replace(hour=11, minute=0).isoformat() + 'Z'
        },
        {
            'title': 'Dev Meeting',
            'start_time': (now + timedelta(days=2)).replace(hour=11, minute=30).isoformat() + 'Z',
            'end_time': (now + timedelta(days=2)).replace(hour=12, minute=30).isoformat() + 'Z'
        },
        # Close events (travel time issue)
        {
            'title': 'Project Review',
            'start_time': (now + timedelta(days=3)).replace(hour=14, minute=0).isoformat() + 'Z',
            'end_time': (now + timedelta(days=3)).replace(hour=14, minute=30).isoformat() + 'Z'
        },
        {
            'title': 'Client Call',
            'start_time': (now + timedelta(days=3)).replace(hour=14, minute=35).isoformat() + 'Z',
            'end_time': (now + timedelta(days=3)).replace(hour=15, minute=30).isoformat() + 'Z'
        },
        # Early morning events
        {
            'title': 'Early Meeting',
            'start_time': (now + timedelta(days=4)).replace(hour=8, minute=0).isoformat() + 'Z',
            'end_time': (now + timedelta(days=4)).replace(hour=8, minute=30).isoformat() + 'Z'
        },
        {
            'title': 'Morning Class',
            'start_time': (now + timedelta(days=5)).replace(hour=8, minute=30).isoformat() + 'Z',
            'end_time': (now + timedelta(days=5)).replace(hour=9, minute=30).isoformat() + 'Z'
        },
    ]


# ============================================================================
# Test BusyTimeAnalyzer
# ============================================================================

class TestBusyTimeAnalyzer:
    """Test pattern detection for busy time blocks."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initializes correctly."""
        analyzer = BusyTimeAnalyzer()
        assert analyzer is not None
        assert isinstance(analyzer.time_blocks, dict)
    
    def test_detect_busy_tuesday_mornings(self):
        """Test detection of consistent Tuesday morning busy pattern."""
        events = get_sample_events()
        analyzer = BusyTimeAnalyzer()
        busy_blocks, patterns = analyzer.analyze(events)
        
        assert len(patterns) > 0
        assert any('Consistent' in p.name for p in patterns)
        assert any('Tuesday' in p.description for p in patterns)
    
    def test_busy_blocks_returned(self):
        """Test that busy blocks are returned correctly."""
        events = get_sample_events()
        analyzer = BusyTimeAnalyzer()
        busy_blocks, patterns = analyzer.analyze(events)
        
        assert len(busy_blocks) > 0
        assert all(isinstance(b, TimeBlock) for b in busy_blocks)
        assert all(hasattr(b, 'day_of_week') for b in busy_blocks)
        assert all(hasattr(b, 'start_hour') for b in busy_blocks)
    
    def test_no_patterns_empty_events(self):
        """Test no patterns detected with empty events."""
        analyzer = BusyTimeAnalyzer()
        busy_blocks, patterns = analyzer.analyze([])
        
        assert len(busy_blocks) == 0
        assert len(patterns) == 0
    
    def test_pattern_confidence_score(self):
        """Test pattern confidence is calculated."""
        events = get_sample_events()
        analyzer = BusyTimeAnalyzer()
        busy_blocks, patterns = analyzer.analyze(events)
        
        if patterns:
            for pattern in patterns:
                assert 0.0 <= pattern.confidence <= 1.0


# ============================================================================
# Test EventProximityAnalyzer
# ============================================================================

class TestEventProximityAnalyzer:
    """Test detection of events too close together."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initializes with min_gap."""
        analyzer = EventProximityAnalyzer(min_gap_minutes=15)
        assert analyzer.min_gap_minutes == 15
    
    def test_detect_close_events(self):
        """Test detection of events with insufficient gap."""
        events = get_sample_events()
        analyzer = EventProximityAnalyzer(min_gap_minutes=15)
        close_pairs, patterns = analyzer.analyze(events)
        
        assert len(close_pairs) > 0
        assert len(patterns) > 0
        assert any('Travel' in p.name for p in patterns)
    
    def test_gap_calculation(self):
        """Test gap between events is calculated correctly."""
        events = get_sample_events()
        analyzer = EventProximityAnalyzer(min_gap_minutes=20)
        close_pairs, patterns = analyzer.analyze(events)
        
        for pair in close_pairs:
            assert 'gap_minutes' in pair
            assert pair['gap_minutes'] < 20
    
    def test_no_issues_large_gaps(self):
        """Test no issues when gaps are large."""
        now = datetime.now()
        events = [
            {
                'title': 'Meeting 1',
                'start_time': now.replace(hour=9).isoformat() + 'Z',
                'end_time': now.replace(hour=10).isoformat() + 'Z'
            },
            {
                'title': 'Meeting 2',
                'start_time': (now + timedelta(hours=3)).replace(hour=13).isoformat() + 'Z',
                'end_time': (now + timedelta(hours=3)).replace(hour=14).isoformat() + 'Z'
            },
        ]
        analyzer = EventProximityAnalyzer(min_gap_minutes=60)
        close_pairs, patterns = analyzer.analyze(events)
        
        assert len(close_pairs) == 0


# ============================================================================
# Test ReminderPatternAnalyzer
# ============================================================================

class TestReminderPatternAnalyzer:
    """Test reminder pattern detection."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initializes."""
        analyzer = ReminderPatternAnalyzer()
        assert analyzer is not None
    
    def test_detect_early_events(self):
        """Test detection of early morning events."""
        events = get_sample_events()
        analyzer = ReminderPatternAnalyzer()
        stats, patterns = analyzer.analyze(events)
        
        assert 'early_events' in stats
        assert stats['early_events'] > 0
    
    def test_early_reminder_pattern(self):
        """Test pattern for early morning events without reminders."""
        events = get_sample_events()
        analyzer = ReminderPatternAnalyzer()
        stats, patterns = analyzer.analyze(events)
        
        if patterns:
            assert any('Early' in p.name for p in patterns)


# ============================================================================
# Test FocusTimeAnalyzer
# ============================================================================

class TestFocusTimeAnalyzer:
    """Test focus time availability detection."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initializes."""
        analyzer = FocusTimeAnalyzer()
        assert analyzer is not None
    
    def test_focus_time_detection(self):
        """Test focus time availability is calculated."""
        events = get_sample_events()
        analyzer = FocusTimeAnalyzer()
        stats, patterns = analyzer.analyze(events)
        
        assert 'focus_available_pct' in stats
        assert 0.0 <= stats['focus_available_pct'] <= 1.0
        assert 'event_minutes' in stats
    
    def test_limited_focus_time_pattern(self):
        """Test pattern detected for limited focus time."""
        # Create a heavily booked week
        now = datetime.now()
        events = []
        for day in range(5):  # 5 days
            for hour in range(9, 18):  # 9am-6pm
                events.append({
                    'title': f'Meeting {day}-{hour}',
                    'start_time': (now + timedelta(days=day)).replace(hour=hour, minute=0).isoformat() + 'Z',
                    'end_time': (now + timedelta(days=day)).replace(hour=hour, minute=50).isoformat() + 'Z'
                })
        
        analyzer = FocusTimeAnalyzer()
        stats, patterns = analyzer.analyze(events)
        
        assert any('Limited' in p.name for p in patterns)


# ============================================================================
# Test BreakPatternAnalyzer
# ============================================================================

class TestBreakPatternAnalyzer:
    """Test break pattern detection."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initializes."""
        analyzer = BreakPatternAnalyzer()
        assert analyzer is not None
    
    def test_back_to_back_detection(self):
        """Test detection of back-to-back events."""
        events = get_sample_events()
        analyzer = BreakPatternAnalyzer()
        stats, patterns = analyzer.analyze(events)
        
        assert 'back_to_back_sequences' in stats
        if patterns:
            assert any('Break' in p.name for p in patterns)


# ============================================================================
# Test AIInsightGenerator
# ============================================================================

class TestAIInsightGenerator:
    """Test insight and prediction generation."""
    
    def test_generator_initialization(self):
        """Test generator initializes."""
        generator = AIInsightGenerator(use_gpt=False)
        assert generator is not None
    
    def test_generate_insights_from_patterns(self):
        """Test predictions are generated from patterns."""
        patterns = [
            Pattern(
                name="Consistent Tuesday Mornings",
                confidence=0.85,
                description="You're busy every Tuesday morning",
                frequency="regular"
            ),
            Pattern(
                name="Travel Time Conflicts",
                confidence=0.75,
                description="Events too close together",
                frequency="occasional"
            )
        ]
        
        generator = AIInsightGenerator(use_gpt=False)
        events = get_sample_events()
        predictions = generator.generate_insights(patterns, events)
        
        assert len(predictions) > 0
        assert all(isinstance(p, Prediction) for p in predictions)
        assert all(hasattr(p, 'category') for p in predictions)
        assert all(hasattr(p, 'recommendation') for p in predictions)
    
    def test_predictions_have_required_fields(self):
        """Test predictions have all required fields."""
        patterns = [
            Pattern(
                name="Consistent Tuesday Mornings",
                confidence=0.9,
                description="Tuesday mornings blocked",
                frequency="regular"
            )
        ]
        
        generator = AIInsightGenerator(use_gpt=False)
        predictions = generator.generate_insights(patterns, get_sample_events())
        
        for pred in predictions:
            assert pred.prediction_id
            assert pred.category in ['learning_blocks', 'travel_time', 'reminder', 'focus_time', 'break']
            assert pred.confidence > 0
            assert pred.priority in ['low', 'medium', 'high']
            assert pred.recommendation


# ============================================================================
# Test PatternPredictionService
# ============================================================================

class TestPatternPredictionService:
    """Test main pattern prediction service."""
    
    def test_service_initialization(self):
        """Test service initializes all analyzers."""
        service = PatternPredictionService(use_gpt=False)
        assert service is not None
        assert service.busy_analyzer is not None
        assert service.proximity_analyzer is not None
        assert service.reminder_analyzer is not None
        assert service.focus_analyzer is not None
        assert service.break_analyzer is not None
    
    def test_comprehensive_analysis(self):
        """Test full calendar analysis."""
        events = get_sample_events()
        service = PatternPredictionService(use_gpt=False)
        result = service.analyze_calendar(events)
        
        assert result['event_count'] == len(events)
        assert 'patterns' in result
        assert 'predictions' in result
        assert 'summary' in result
        assert 'generated_at' in result
    
    def test_patterns_detected(self):
        """Test patterns are detected in analysis."""
        events = get_sample_events()
        service = PatternPredictionService(use_gpt=False)
        result = service.analyze_calendar(events)
        
        assert len(result['patterns']) > 0
        for pattern in result['patterns']:
            assert 'name' in pattern
            assert 'confidence' in pattern
            assert 'description' in pattern
            assert 'frequency' in pattern
    
    def test_predictions_generated(self):
        """Test predictions are generated."""
        events = get_sample_events()
        service = PatternPredictionService(use_gpt=False)
        result = service.analyze_calendar(events)
        
        assert len(result['predictions']) > 0
        for pred in result['predictions']:
            assert 'id' in pred
            assert 'category' in pred
            assert 'insight' in pred
            assert 'recommendation' in pred
            assert 'actionable' in pred
            assert 'priority' in pred
            assert 'confidence' in pred
    
    def test_predictions_sorted_by_priority(self):
        """Test predictions are sorted by priority."""
        events = get_sample_events()
        service = PatternPredictionService(use_gpt=False)
        result = service.analyze_calendar(events)
        
        predictions = result['predictions']
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        
        for i in range(len(predictions) - 1):
            current = priority_order.get(predictions[i]['priority'], 3)
            next_item = priority_order.get(predictions[i + 1]['priority'], 3)
            assert current <= next_item  # High priority comes first
    
    def test_empty_calendar(self):
        """Test handling of empty calendar."""
        service = PatternPredictionService(use_gpt=False)
        result = service.analyze_calendar([])
        
        assert result['event_count'] == 0
        assert 'patterns' in result
        assert 'predictions' in result
    
    def test_apply_prediction(self):
        """Test applying a prediction."""
        events = get_sample_events()
        service = PatternPredictionService(use_gpt=False)
        result = service.analyze_calendar(events)
        
        if result['predictions']:
            first_pred_id = result['predictions'][0]['id']
            # Create a prediction object from dict
            pred = Prediction(
                prediction_id=first_pred_id,
                category=result['predictions'][0]['category'],
                insight=result['predictions'][0]['insight'],
                recommendation=result['predictions'][0]['recommendation'],
                actionable=True,
                priority=result['predictions'][0]['priority'],
                confidence=result['predictions'][0]['confidence'] / 100.0
            )
            
            action_plan = service.apply_prediction(pred, events)
            
            assert action_plan['prediction_id'] == first_pred_id
            assert 'actions' in action_plan
            assert 'status' in action_plan
            assert len(action_plan['actions']) > 0
    
    def test_summary_generation(self):
        """Test summary text is generated."""
        events = get_sample_events()
        service = PatternPredictionService(use_gpt=False)
        result = service.analyze_calendar(events)
        
        assert result['summary']
        assert len(result['summary']) > 0
        assert isinstance(result['summary'], str)


# ============================================================================
# Integration Tests
# ============================================================================

class TestPatternAnalysisIntegration:
    """Integration tests for full pattern analysis workflow."""
    
    def test_full_workflow(self):
        """Test complete pattern detection to action workflow."""
        events = get_sample_events()
        service = PatternPredictionService(use_gpt=False, min_gap_minutes=15)
        
        # Step 1: Analyze
        analysis = service.analyze_calendar(events)
        assert analysis['status'] not in ['error']
        assert len(analysis['patterns']) > 0
        
        # Step 2: Get predictions
        predictions = analysis['predictions']
        assert len(predictions) > 0
        
        # Step 3: Apply first prediction
        if predictions:
            pred = Prediction(
                prediction_id=predictions[0]['id'],
                category=predictions[0]['category'],
                insight=predictions[0]['insight'],
                recommendation=predictions[0]['recommendation'],
                actionable=True,
                priority=predictions[0]['priority'],
                confidence=predictions[0]['confidence'] / 100.0
            )
            
            action_plan = service.apply_prediction(pred, events)
            assert action_plan['status'] == 'ready'
            assert len(action_plan['actions']) > 0
    
    def test_multiple_pattern_detection(self):
        """Test multiple patterns detected in realistic calendar."""
        events = get_sample_events()
        service = PatternPredictionService(use_gpt=False)
        analysis = service.analyze_calendar(events)
        
        # Should detect multiple patterns from diverse events
        pattern_names = [p['name'] for p in analysis['patterns']]
        assert len(pattern_names) >= 2  # At least 2 different pattern types
    
    def test_high_priority_predictions_first(self):
        """Test high-priority predictions appear first."""
        events = get_sample_events()
        service = PatternPredictionService(use_gpt=False)
        analysis = service.analyze_calendar(events)
        
        predictions = analysis['predictions']
        high_priority = [p for p in predictions if p['priority'] == 'high']
        
        if high_priority:
            first_is_high = predictions[0]['priority'] == 'high'
            assert first_is_high


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_malformed_event_datetime(self):
        """Test handling of malformed datetime."""
        events = [
            {
                'title': 'Bad Event',
                'start_time': 'not-a-date',
                'end_time': 'also-not-a-date'
            }
        ]
        
        service = PatternPredictionService(use_gpt=False)
        result = service.analyze_calendar(events)
        
        # Should not crash, returns 0 events analyzed
        assert result['event_count'] == 1
    
    def test_missing_event_fields(self):
        """Test handling of events with missing fields."""
        events = [
            {'title': 'No dates event'},  # Missing start/end times
            {
                'start_time': datetime.now().isoformat() + 'Z',
                'end_time': datetime.now().isoformat() + 'Z'
                # Missing title
            }
        ]
        
        service = PatternPredictionService(use_gpt=False)
        result = service.analyze_calendar(events)
        
        # Should handle gracefully
        assert 'patterns' in result
        assert 'predictions' in result
    
    def test_single_event(self):
        """Test analysis with single event."""
        now = datetime.now()
        events = [
            {
                'title': 'Single Event',
                'start_time': now.replace(hour=10).isoformat() + 'Z',
                'end_time': now.replace(hour=11).isoformat() + 'Z'
            }
        ]
        
        service = PatternPredictionService(use_gpt=False)
        result = service.analyze_calendar(events)
        
        assert result['event_count'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
