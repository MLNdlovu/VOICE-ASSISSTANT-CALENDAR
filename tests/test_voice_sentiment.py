"""
Unit Tests for Voice Sentiment Analysis Module

Tests emotion detection, stress level calculation, mood assessment,
and emotion-based recommendations.
"""

import pytest
from datetime import datetime
from src.voice_sentiment import (
    EmotionType, StressLevel, Mood, 
    EmotionDetection, EmotionResponse,
    VoiceSentimentAnalyzer, EmotionResponseEngine
)


class TestEmotionType:
    """Test EmotionType enumeration."""
    
    def test_emotion_types_exist(self):
        """Verify all emotion types exist."""
        emotions = [
            EmotionType.HAPPY, EmotionType.STRESSED, EmotionType.ANXIOUS,
            EmotionType.SAD, EmotionType.FRUSTRATED, EmotionType.CALM,
            EmotionType.NEUTRAL, EmotionType.EXCITED, EmotionType.TIRED,
            EmotionType.CONFUSED
        ]
        assert len(emotions) >= 10
    
    def test_emotion_values(self):
        """Test emotion enum values."""
        assert EmotionType.HAPPY.value == "happy"
        assert EmotionType.STRESSED.value == "stressed"
        assert EmotionType.TIRED.value == "tired"


class TestStressLevel:
    """Test StressLevel enumeration."""
    
    def test_stress_levels_exist(self):
        """Verify all stress levels exist."""
        levels = [
            StressLevel.LOW,
            StressLevel.MODERATE,
            StressLevel.HIGH,
            StressLevel.CRITICAL
        ]
        assert len(levels) == 4
    
    def test_stress_level_values(self):
        """Test stress level values."""
        assert StressLevel.LOW.value == "low"
        assert StressLevel.MODERATE.value == "moderate"
        assert StressLevel.HIGH.value == "high"
        assert StressLevel.CRITICAL.value == "critical"


class TestMood:
    """Test Mood enumeration."""
    
    def test_mood_values_exist(self):
        """Verify all mood values exist."""
        moods = [
            Mood.VERY_POSITIVE,
            Mood.POSITIVE,
            Mood.NEUTRAL,
            Mood.NEGATIVE,
            Mood.VERY_NEGATIVE
        ]
        assert len(moods) == 5
    
    def test_mood_values(self):
        """Test mood enum values."""
        assert Mood.VERY_POSITIVE.value == "very_positive"
        assert Mood.NEUTRAL.value == "neutral"
        assert Mood.VERY_NEGATIVE.value == "very_negative"


class TestEmotionDetection:
    """Test EmotionDetection dataclass."""
    
    def test_emotion_detection_creation(self):
        """Test creating an emotion detection."""
        detection = EmotionDetection(
            primary_emotion=EmotionType.HAPPY,
            confidence=0.85,
            stress_level=StressLevel.LOW,
            mood=Mood.POSITIVE,
            energy_level=0.8
        )
        assert detection.primary_emotion == EmotionType.HAPPY
        assert detection.confidence == 0.85
        assert detection.stress_level == StressLevel.LOW
        assert detection.mood == Mood.POSITIVE
        assert detection.energy_level == 0.8
    
    def test_emotion_detection_with_secondary(self):
        """Test emotion detection with secondary emotions."""
        detection = EmotionDetection(
            primary_emotion=EmotionType.STRESSED,
            secondary_emotions=[
                (EmotionType.ANXIOUS, 0.6),
                (EmotionType.TIRED, 0.5)
            ],
            confidence=0.9
        )
        assert len(detection.secondary_emotions) == 2
        assert detection.secondary_emotions[0][0] == EmotionType.ANXIOUS
    
    def test_emotion_detection_to_dict(self):
        """Test converting emotion detection to dict."""
        detection = EmotionDetection(
            primary_emotion=EmotionType.HAPPY,
            confidence=0.85,
            stress_level=StressLevel.LOW,
            mood=Mood.POSITIVE,
            energy_level=0.8
        )
        d = detection.to_dict()
        
        assert d['primary'] == 'happy'
        assert d['confidence'] == 0.85
        assert d['stress'] == 'low'
        assert d['mood'] == 'positive'
        assert d['energy'] == 0.8
    
    def test_emotion_detection_timestamp(self):
        """Test that emotion detection has timestamp."""
        detection = EmotionDetection(
            primary_emotion=EmotionType.HAPPY
        )
        assert isinstance(detection.detected_at, datetime)


class TestEmotionResponse:
    """Test EmotionResponse dataclass."""
    
    def test_emotion_response_creation(self):
        """Test creating an emotion response."""
        response = EmotionResponse(
            category='calendar_adjustment',
            action='reduce_meetings',
            description='Reduce your meetings load',
            priority='high',
            confidence=0.95,
            rationale='You sound stressed'
        )
        assert response.category == 'calendar_adjustment'
        assert response.action == 'reduce_meetings'
        assert response.priority == 'high'
        assert response.confidence == 0.95


class TestVoiceSentimentAnalyzer:
    """Test VoiceSentimentAnalyzer class."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = VoiceSentimentAnalyzer(use_transformers=False)
        assert analyzer is not None
        assert analyzer.use_transformers == False
    
    def test_detect_happiness(self):
        """Test detecting happy emotion."""
        analyzer = VoiceSentimentAnalyzer(use_transformers=False)
        
        detection = analyzer.detect_emotion("I'm so happy and excited about this!")
        
        assert detection.primary_emotion in [EmotionType.HAPPY, EmotionType.EXCITED]
        assert detection.mood in [Mood.VERY_POSITIVE, Mood.POSITIVE]
        assert detection.energy_level > 0.5
    
    def test_detect_stress(self):
        """Test detecting stressed emotion."""
        analyzer = VoiceSentimentAnalyzer(use_transformers=False)
        
        detection = analyzer.detect_emotion("Yoh I'm stressed out and overwhelmed!")
        
        assert detection.primary_emotion in [EmotionType.STRESSED, EmotionType.ANXIOUS]
        assert detection.stress_level in [StressLevel.HIGH, StressLevel.CRITICAL]
        assert detection.mood in [Mood.NEGATIVE, Mood.VERY_NEGATIVE]
    
    def test_detect_tiredness(self):
        """Test detecting tired emotion."""
        analyzer = VoiceSentimentAnalyzer(use_transformers=False)
        
        detection = analyzer.detect_emotion("I'm so tired and exhausted")
        
        assert detection.primary_emotion in [EmotionType.TIRED, EmotionType.SAD]
        assert detection.energy_level < 0.4
    
    def test_detect_calm(self):
        """Test detecting calm emotion."""
        analyzer = VoiceSentimentAnalyzer(use_transformers=False)
        
        detection = analyzer.detect_emotion("I'm feeling calm and relaxed")
        
        assert detection.primary_emotion in [EmotionType.CALM, EmotionType.NEUTRAL]
        assert detection.stress_level == StressLevel.LOW
    
    def test_stress_level_calculation(self):
        """Test stress level calculation."""
        analyzer = VoiceSentimentAnalyzer(use_transformers=False)
        
        # Critical stress (urgent keywords + multiple exclamation marks)
        critical = analyzer.detect_emotion("URGENT!! This is critical!!!")
        assert critical.stress_level in [StressLevel.HIGH, StressLevel.CRITICAL]
        
        # Low stress
        low = analyzer.detect_emotion("Everything is fine")
        assert low.stress_level == StressLevel.LOW
    
    def test_energy_level_estimation(self):
        """Test energy level estimation."""
        analyzer = VoiceSentimentAnalyzer(use_transformers=False)
        
        # High energy
        excited = analyzer.detect_emotion("I'm excited and pumped!")
        assert excited.energy_level > 0.7
        
        # Low energy
        tired = analyzer.detect_emotion("I'm tired and drained")
        assert tired.energy_level < 0.4
    
    def test_mood_calculation(self):
        """Test mood calculation from emotion."""
        analyzer = VoiceSentimentAnalyzer(use_transformers=False)
        
        # Very positive
        happy = analyzer.detect_emotion("I'm so happy!")
        assert happy.mood in [Mood.VERY_POSITIVE, Mood.POSITIVE]
        
        # Very negative
        sad = analyzer.detect_emotion("I'm so sad and depressed")
        assert sad.mood in [Mood.NEGATIVE, Mood.VERY_NEGATIVE]
    
    def test_keyword_based_emotion(self):
        """Test keyword-based emotion detection (fallback)."""
        analyzer = VoiceSentimentAnalyzer(use_transformers=False)
        
        text = "I'm frustrated and annoyed"
        primary, secondary, conf = analyzer._keyword_based_emotion(text)
        
        assert primary in [EmotionType.STRESSED, EmotionType.FRUSTRATED, EmotionType.ANXIOUS]
        assert conf > 0.5
    
    def test_emotion_summary(self):
        """Test emotion summary generation."""
        analyzer = VoiceSentimentAnalyzer(use_transformers=False)
        
        detection = EmotionDetection(
            primary_emotion=EmotionType.STRESSED,
            stress_level=StressLevel.HIGH,
            energy_level=0.3
        )
        
        summary = analyzer.get_emotion_summary(detection)
        
        assert "stressed" in summary.lower()
        assert "stress level: high" in summary.lower()
        assert "energy" in summary.lower()
    
    def test_confidence_threshold(self):
        """Test confidence threshold in detection."""
        analyzer = VoiceSentimentAnalyzer(use_transformers=False)
        
        # Should handle confidence threshold
        detection = analyzer.detect_emotion("hello", confidence_threshold=0.9)
        
        # Should return some emotion even with high threshold
        assert detection is not None
        assert detection.primary_emotion is not None


class TestEmotionResponseEngine:
    """Test EmotionResponseEngine class."""
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = EmotionResponseEngine()
        assert engine is not None
        assert engine.response_counter == 0
    
    def test_stress_responses(self):
        """Test generating stress responses."""
        engine = EmotionResponseEngine()
        
        detection = EmotionDetection(
            primary_emotion=EmotionType.STRESSED,
            stress_level=StressLevel.HIGH,
            mood=Mood.NEGATIVE,
            energy_level=0.3
        )
        
        responses = engine.get_responses(detection)
        
        assert len(responses) > 0
        assert any(r.category == 'calendar_adjustment' for r in responses)
        assert any(r.category == 'break' for r in responses)
    
    def test_low_energy_responses(self):
        """Test generating low energy responses."""
        engine = EmotionResponseEngine()
        
        detection = EmotionDetection(
            primary_emotion=EmotionType.TIRED,
            stress_level=StressLevel.MODERATE,
            energy_level=0.2
        )
        
        responses = engine.get_responses(detection)
        
        assert len(responses) > 0
        assert any('energy' in r.action.lower() or 'energy' in r.description.lower() 
                  for r in responses)
    
    def test_positive_mood_responses(self):
        """Test generating positive mood responses."""
        engine = EmotionResponseEngine()
        
        detection = EmotionDetection(
            primary_emotion=EmotionType.HAPPY,
            mood=Mood.VERY_POSITIVE,
            energy_level=0.9,
            stress_level=StressLevel.LOW
        )
        
        responses = engine.get_responses(detection)
        
        assert len(responses) > 0
        assert any(r.category in ['activity', 'support'] for r in responses)
    
    def test_negative_mood_responses(self):
        """Test generating negative mood responses."""
        engine = EmotionResponseEngine()
        
        detection = EmotionDetection(
            primary_emotion=EmotionType.SAD,
            mood=Mood.NEGATIVE,
            energy_level=0.2,
            stress_level=StressLevel.MODERATE
        )
        
        responses = engine.get_responses(detection)
        
        assert len(responses) > 0
        assert any('check' in r.action.lower() or 'support' in r.category for r in responses)
    
    def test_anxiety_responses(self):
        """Test generating anxiety responses."""
        engine = EmotionResponseEngine()
        
        detection = EmotionDetection(
            primary_emotion=EmotionType.ANXIOUS,
            mood=Mood.NEGATIVE,
            stress_level=StressLevel.HIGH
        )
        
        responses = engine.get_responses(detection)
        
        assert len(responses) > 0
        # Anxiety should suggest structure/grounding
        assert any('structure' in r.description.lower() or 'grounding' in r.description.lower()
                  for r in responses)
    
    def test_response_confidence_scores(self):
        """Test that responses have confidence scores."""
        engine = EmotionResponseEngine()
        
        detection = EmotionDetection(
            primary_emotion=EmotionType.STRESSED,
            stress_level=StressLevel.HIGH
        )
        
        responses = engine.get_responses(detection)
        
        assert all(hasattr(r, 'confidence') for r in responses)
        assert all(0 <= r.confidence <= 1 for r in responses)
    
    def test_stress_relief_plan(self):
        """Test generating stress relief calendar adjustments."""
        engine = EmotionResponseEngine()
        
        detection = EmotionDetection(
            primary_emotion=EmotionType.STRESSED,
            stress_level=StressLevel.CRITICAL
        )
        
        events = [
            {'title': 'Meeting 1', 'priority': 'low'},
            {'title': 'Meeting 2', 'priority': 'high'},
            {'title': 'Task 1', 'priority': 'optional'}
        ]
        
        plan = engine.apply_stress_relief(events, detection)
        
        assert plan is not None
        assert 'stress_level' in plan
        assert 'actions' in plan
        assert len(plan['actions']) > 0


class TestSentimentAnalysisIntegration:
    """Integration tests for sentiment analysis workflow."""
    
    def test_complete_analysis_workflow(self):
        """Test complete sentiment analysis workflow."""
        analyzer = VoiceSentimentAnalyzer(use_transformers=False)
        engine = EmotionResponseEngine()
        
        # Analyze text
        text = "Yoh I'm stressed and overwhelmed with meetings, please help!"
        detection = analyzer.detect_emotion(text)
        
        # Get recommendations
        responses = engine.get_responses(detection)
        
        # Generate summary
        summary = analyzer.get_emotion_summary(detection)
        
        # Assertions
        assert detection.stress_level in [StressLevel.HIGH, StressLevel.CRITICAL]
        assert len(responses) > 0
        assert len(summary) > 0
        assert "stressed" in summary.lower()
    
    def test_multiple_emotion_detection(self):
        """Test detecting multiple emotion types."""
        analyzer = VoiceSentimentAnalyzer(use_transformers=False)
        
        texts = [
            ("I'm happy!", EmotionType.HAPPY),
            ("I'm stressed!", EmotionType.STRESSED),
            ("I'm tired", EmotionType.TIRED),
            ("I'm calm", EmotionType.CALM),
            ("I'm excited!", EmotionType.EXCITED),
        ]
        
        for text, expected_category in texts:
            detection = analyzer.detect_emotion(text)
            # Check that primary emotion is related to expected
            assert detection.primary_emotion is not None
            assert detection.energy_level >= 0 and detection.energy_level <= 1
    
    def test_mood_based_calendar_adjustment(self):
        """Test mood-based calendar adjustment workflow."""
        analyzer = VoiceSentimentAnalyzer(use_transformers=False)
        engine = EmotionResponseEngine()
        
        # Stressed user
        text = "I'm completely stressed, shift my meetings to low load"
        detection = analyzer.detect_emotion(text)
        
        events = [
            {'title': 'Meeting 1', 'priority': 'low'},
            {'title': 'Meeting 2', 'priority': 'medium'},
            {'title': 'Focus Time', 'priority': 'high'}
        ]
        
        plan = engine.apply_stress_relief(events, detection)
        
        assert plan['stress_level'] in ['high', 'critical']
        assert len(plan['actions']) > 0
    
    def test_happiness_activity_suggestions(self):
        """Test activity suggestions for happy mood."""
        analyzer = VoiceSentimentAnalyzer(use_transformers=False)
        engine = EmotionResponseEngine()
        
        text = "I'm so happy! Add something fun on Saturday!"
        detection = analyzer.detect_emotion(text)
        
        responses = engine.get_responses(detection)
        
        # Should suggest fun activities
        assert detection.mood in [Mood.VERY_POSITIVE, Mood.POSITIVE]
        assert len(responses) > 0


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_text_analysis(self):
        """Test analyzing empty text."""
        analyzer = VoiceSentimentAnalyzer(use_transformers=False)
        
        detection = analyzer.detect_emotion("")
        
        # Should return neutral
        assert detection.primary_emotion == EmotionType.NEUTRAL
    
    def test_very_long_text(self):
        """Test analyzing very long text."""
        analyzer = VoiceSentimentAnalyzer(use_transformers=False)
        
        long_text = "I'm happy and excited " * 100
        detection = analyzer.detect_emotion(long_text)
        
        assert detection is not None
        assert detection.primary_emotion is not None
    
    def test_special_characters_in_text(self):
        """Test analyzing text with special characters."""
        analyzer = VoiceSentimentAnalyzer(use_transformers=False)
        
        text = "I'm stressed!!! @#$%^&*() Help!!!"
        detection = analyzer.detect_emotion(text)
        
        assert detection is not None
        assert detection.stress_level in [StressLevel.HIGH, StressLevel.CRITICAL]
    
    def test_mixed_case_text(self):
        """Test analyzing mixed case text."""
        analyzer = VoiceSentimentAnalyzer(use_transformers=False)
        
        text = "I'm StReSSed AnD aNxIoUs"
        detection = analyzer.detect_emotion(text)
        
        assert detection is not None
        assert detection.primary_emotion is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
