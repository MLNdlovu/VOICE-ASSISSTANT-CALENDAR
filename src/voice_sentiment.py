"""
Voice Sentiment & Emotion Analysis Module

Detects emotion, stress level, and mood from voice input.
Provides emotion-aware calendar recommendations and interventions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    pipeline = None


# ============================================================================
# Data Structures & Enums
# ============================================================================

class EmotionType(Enum):
    """Detected emotions."""
    HAPPY = "happy"
    STRESSED = "stressed"
    ANXIOUS = "anxious"
    SAD = "sad"
    FRUSTRATED = "frustrated"
    CALM = "calm"
    NEUTRAL = "neutral"
    EXCITED = "excited"
    TIRED = "tired"
    CONFUSED = "confused"


class StressLevel(Enum):
    """Detected stress levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class Mood(Enum):
    """Overall mood assessment."""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


@dataclass
class EmotionDetection:
    """Detected emotions from voice/text."""
    primary_emotion: EmotionType
    secondary_emotions: List[Tuple[EmotionType, float]] = field(default_factory=list)
    confidence: float = 0.0
    stress_level: StressLevel = StressLevel.MODERATE
    mood: Mood = Mood.NEUTRAL
    energy_level: float = 0.5  # 0-1 scale
    detected_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        return {
            'primary': self.primary_emotion.value,
            'secondary': [(e.value, c) for e, c in self.secondary_emotions],
            'confidence': self.confidence,
            'stress': self.stress_level.value,
            'mood': self.mood.value,
            'energy': self.energy_level
        }


@dataclass
class EmotionResponse:
    """Recommended action based on emotion detection."""
    category: str  # 'calendar_adjustment', 'support', 'break', 'activity'
    action: str
    description: str
    priority: str  # 'high', 'medium', 'low'
    confidence: float
    rationale: str


# ============================================================================
# Sentiment Analyzer
# ============================================================================

class VoiceSentimentAnalyzer:
    """Analyzes emotion and stress from voice commands."""
    
    def __init__(self, use_transformers: bool = True):
        self.use_transformers = use_transformers and TRANSFORMERS_AVAILABLE
        self.emotion_classifier = None
        self.text_classifier = None
        
        if self.use_transformers:
            self._init_classifiers()
    
    def _init_classifiers(self):
        """Initialize HuggingFace transformers."""
        try:
            # Emotion classification model
            self.emotion_classifier = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                top_k=None
            )
            # Sentiment classification model
            self.text_classifier = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )
        except Exception as e:
            print(f"[WARN] Could not load transformers: {e}")
            self.use_transformers = False
    
    def detect_emotion(self, text: str, confidence_threshold: float = 0.5) -> EmotionDetection:
        """
        Detect emotions from text.
        
        Args:
            text: Voice transcribed text or direct input
            confidence_threshold: Minimum confidence to report emotion
            
        Returns:
            EmotionDetection object with detected emotions
        """
        primary_emotion = EmotionType.NEUTRAL
        secondary_emotions = []
        confidence = 0.0
        stress_level = StressLevel.MODERATE
        mood = Mood.NEUTRAL
        energy_level = 0.5
        
        # If transformers available, use ML detection
        if self.use_transformers and self.emotion_classifier:
            try:
                results = self.emotion_classifier(text[:512])  # Limit input
                
                if results and len(results) > 0:
                    # Get primary emotion
                    top_result = results[0][0] if isinstance(results[0], list) else results[0]
                    primary_emotion = self._map_emotion(top_result.get('label', 'neutral'))
                    confidence = top_result.get('score', 0.0)
                    
                    # Get secondary emotions
                    if isinstance(results[0], list):
                        for result in results[0][1:3]:  # Top 3
                            if result.get('score', 0) >= confidence_threshold:
                                secondary_emotions.append((
                                    self._map_emotion(result.get('label', 'neutral')),
                                    result.get('score', 0)
                                ))
            except Exception as e:
                print(f"[WARN] Emotion detection error: {e}")
        
        # Fallback: keyword-based detection
        if confidence < 0.4 or not self.use_transformers:
            primary_emotion, secondary_emotions, confidence = self._keyword_based_emotion(text)
        
        # Determine stress level
        stress_level = self._calculate_stress_level(text, primary_emotion)
        
        # Calculate mood
        mood = self._calculate_mood(primary_emotion, stress_level)
        
        # Estimate energy level
        energy_level = self._estimate_energy(primary_emotion, stress_level)
        
        return EmotionDetection(
            primary_emotion=primary_emotion,
            secondary_emotions=secondary_emotions,
            confidence=confidence,
            stress_level=stress_level,
            mood=mood,
            energy_level=energy_level
        )
    
    def _map_emotion(self, label: str) -> EmotionType:
        """Map HuggingFace emotion labels to our enum."""
        label_lower = label.lower()
        
        mapping = {
            'joy': EmotionType.HAPPY,
            'happy': EmotionType.HAPPY,
            'excitement': EmotionType.EXCITED,
            'excited': EmotionType.EXCITED,
            'fear': EmotionType.ANXIOUS,
            'anxiety': EmotionType.ANXIOUS,
            'anger': EmotionType.FRUSTRATED,
            'frustrated': EmotionType.FRUSTRATED,
            'sadness': EmotionType.SAD,
            'sad': EmotionType.SAD,
            'surprise': EmotionType.EXCITED,
            'disgust': EmotionType.FRUSTRATED,
            'neutral': EmotionType.NEUTRAL,
        }
        
        for key, emotion in mapping.items():
            if key in label_lower:
                return emotion
        
        return EmotionType.NEUTRAL
    
    def _keyword_based_emotion(self, text: str) -> Tuple[EmotionType, List[Tuple[EmotionType, float]], float]:
        """Fallback keyword-based emotion detection."""
        text_lower = text.lower()
        
        # Emotion keywords with confidence
        emotion_keywords = {
            EmotionType.STRESSED: ['stressed', 'stressed out', 'overwhelmed', 'pressure', 'yoh', 'man', 'urgent'],
            EmotionType.ANXIOUS: ['worried', 'anxious', 'nervous', 'concerned', 'freaking out'],
            EmotionType.HAPPY: ['happy', 'great', 'amazing', 'awesome', 'love it', 'wonderful'],
            EmotionType.EXCITED: ['excited', 'stoked', 'pumped', 'hyped', 'fantastic'],
            EmotionType.FRUSTRATED: ['frustrated', 'annoyed', 'irritated', 'angry', 'ugh'],
            EmotionType.TIRED: ['tired', 'exhausted', 'drained', 'burned out', 'fatigue'],
            EmotionType.SAD: ['sad', 'down', 'depressed', 'unhappy', 'miserable'],
            EmotionType.CALM: ['calm', 'relaxed', 'chill', 'peaceful'],
        }
        
        detected = []
        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected.append((emotion, 0.8))
                    break
        
        if not detected:
            return EmotionType.NEUTRAL, [], 0.5
        
        # Sort by emotion priority
        primary = detected[0]
        secondary = detected[1:] if len(detected) > 1 else []
        
        return primary[0], secondary, primary[1]
    
    def _calculate_stress_level(self, text: str, emotion: EmotionType) -> StressLevel:
        """Calculate stress level from text and emotion."""
        text_lower = text.lower()
        stress_score = 0.0
        
        # Emotion-based stress
        if emotion in [EmotionType.STRESSED, EmotionType.ANXIOUS, EmotionType.FRUSTRATED]:
            stress_score += 0.8
        elif emotion in [EmotionType.TIRED, EmotionType.SAD]:
            stress_score += 0.6
        elif emotion in [EmotionType.CALM, EmotionType.HAPPY]:
            stress_score = 0.0
        else:
            stress_score += 0.4
        
        # Keyword-based stress indicators
        urgent_keywords = ['urgent', 'asap', 'immediately', 'crisis', 'emergency', 'critical']
        if any(keyword in text_lower for keyword in urgent_keywords):
            stress_score += 0.3
        
        # Exclamation marks
        exclamation_count = text.count('!')
        if exclamation_count > 2:
            stress_score += 0.2
        
        # Normalize to 0-1
        stress_score = min(1.0, stress_score)
        
        # Map to level
        if stress_score >= 0.8:
            return StressLevel.CRITICAL
        elif stress_score >= 0.6:
            return StressLevel.HIGH
        elif stress_score >= 0.4:
            return StressLevel.MODERATE
        else:
            return StressLevel.LOW
    
    def _calculate_mood(self, emotion: EmotionType, stress: StressLevel) -> Mood:
        """Calculate overall mood from emotion and stress."""
        if emotion in [EmotionType.HAPPY, EmotionType.EXCITED]:
            return Mood.VERY_POSITIVE if stress == StressLevel.LOW else Mood.POSITIVE
        
        elif emotion in [EmotionType.CALM]:
            return Mood.POSITIVE
        
        elif emotion in [EmotionType.STRESSED, EmotionType.ANXIOUS, EmotionType.FRUSTRATED]:
            if stress == StressLevel.CRITICAL:
                return Mood.VERY_NEGATIVE
            elif stress == StressLevel.HIGH:
                return Mood.NEGATIVE
            else:
                return Mood.NEUTRAL
        
        elif emotion in [EmotionType.TIRED, EmotionType.SAD]:
            return Mood.NEGATIVE
        
        else:
            return Mood.NEUTRAL
    
    def _estimate_energy(self, emotion: EmotionType, stress: StressLevel) -> float:
        """Estimate energy level (0-1)."""
        if emotion == EmotionType.EXCITED:
            return 0.9
        elif emotion in [EmotionType.HAPPY, EmotionType.CALM]:
            return 0.7
        elif emotion in [EmotionType.TIRED, EmotionType.SAD]:
            return 0.2
        elif emotion in [EmotionType.STRESSED, EmotionType.ANXIOUS]:
            return 0.4  # Stress uses energy
        elif emotion == EmotionType.FRUSTRATED:
            return 0.3
        else:
            return 0.5
    
    def get_emotion_summary(self, detection: EmotionDetection) -> str:
        """Get human-readable emotion summary."""
        summary = f"I detect you're feeling {detection.primary_emotion.value}"
        
        if detection.secondary_emotions:
            secondary_names = [e.value for e, _ in detection.secondary_emotions[:2]]
            if secondary_names:
                summary += f", with hints of {' and '.join(secondary_names)}"
        
        summary += f". Stress level: {detection.stress_level.value}. Energy: {int(detection.energy_level * 100)}%"
        
        return summary


# ============================================================================
# Emotion-Based Recommendations
# ============================================================================

class EmotionResponseEngine:
    """Generates calendar adjustments based on emotion."""
    
    def __init__(self):
        self.response_counter = 0
    
    def get_responses(self, detection: EmotionDetection) -> List[EmotionResponse]:
        """
        Generate recommended actions based on emotion.
        
        Args:
            detection: EmotionDetection object
            
        Returns:
            List of recommended EmotionResponse objects
        """
        responses = []
        
        # High stress → calendar adjustment
        if detection.stress_level in [StressLevel.HIGH, StressLevel.CRITICAL]:
            responses.extend(self._stress_responses(detection))
        
        # Low energy → break/rest
        if detection.energy_level < 0.3:
            responses.extend(self._low_energy_responses(detection))
        
        # Happy mood → proactive suggestions
        if detection.mood in [Mood.VERY_POSITIVE, Mood.POSITIVE]:
            responses.extend(self._positive_mood_responses(detection))
        
        # Negative mood → support
        if detection.mood in [Mood.NEGATIVE, Mood.VERY_NEGATIVE]:
            responses.extend(self._negative_mood_responses(detection))
        
        # Anxious/Confused → structure
        if detection.primary_emotion in [EmotionType.ANXIOUS, EmotionType.CONFUSED]:
            responses.extend(self._anxiety_responses(detection))
        
        return responses
    
    def _stress_responses(self, detection: EmotionDetection) -> List[EmotionResponse]:
        """Responses for stressed users."""
        responses = []
        
        self.response_counter += 1
        responses.append(EmotionResponse(
            category='calendar_adjustment',
            action='reduce_meetings',
            description='Reduce your meetings load - reschedule non-urgent events to later this week',
            priority='high' if detection.stress_level == StressLevel.CRITICAL else 'medium',
            confidence=0.95,
            rationale='You sound stressed. A lighter calendar might help you regain control.'
        ))
        
        self.response_counter += 1
        responses.append(EmotionResponse(
            category='break',
            action='schedule_break',
            description='Add a 30-minute break to decompress - go for a walk, meditate, or grab coffee',
            priority='high',
            confidence=0.90,
            rationale='A break can help reset and reduce stress levels.'
        ))
        
        if detection.stress_level == StressLevel.CRITICAL:
            self.response_counter += 1
            responses.append(EmotionResponse(
                category='support',
                action='reach_out',
                description='Consider reaching out to a colleague or mentor for support',
                priority='high',
                confidence=0.85,
                rationale='You sound overwhelmed. Support from others might help.'
            ))
        
        return responses
    
    def _low_energy_responses(self, detection: EmotionDetection) -> List[EmotionResponse]:
        """Responses for low energy/tired users."""
        responses = []
        
        self.response_counter += 1
        responses.append(EmotionResponse(
            category='activity',
            action='energy_boost',
            description='Light snack, short walk, or 5-minute exercise to boost energy',
            priority='medium',
            confidence=0.88,
            rationale='A quick energy boost might help you refocus.'
        ))
        
        self.response_counter += 1
        responses.append(EmotionResponse(
            category='calendar_adjustment',
            action='reschedule_heavy_tasks',
            description='Reschedule demanding tasks to when you have more energy',
            priority='medium',
            confidence=0.85,
            rationale='Scheduling important work when you\'re fresher will improve quality.'
        ))
        
        return responses
    
    def _positive_mood_responses(self, detection: EmotionDetection) -> List[EmotionResponse]:
        """Responses for happy/excited users."""
        responses = []
        
        self.response_counter += 1
        responses.append(EmotionResponse(
            category='activity',
            action='plan_fun',
            description='Add something enjoyable to your calendar - social event, hobby, or celebration',
            priority='low',
            confidence=0.80,
            rationale='Harness your positive mood - you\'re in a great space for planning fun things!'
        ))
        
        self.response_counter += 1
        responses.append(EmotionResponse(
            category='activity',
            action='tackle_hard_task',
            description='Channel this energy into tackling a challenging task you\'ve been avoiding',
            priority='medium',
            confidence=0.85,
            rationale='Your positive energy is perfect for facing difficult challenges.'
        ))
        
        return responses
    
    def _negative_mood_responses(self, detection: EmotionDetection) -> List[EmotionResponse]:
        """Responses for sad/negative mood."""
        responses = []
        
        self.response_counter += 1
        responses.append(EmotionResponse(
            category='support',
            action='check_in',
            description='Check in with a friend or colleague - you might benefit from a chat',
            priority='medium',
            confidence=0.88,
            rationale='Connection with others can lift your spirits.'
        ))
        
        self.response_counter += 1
        responses.append(EmotionResponse(
            category='activity',
            action='comfort_activity',
            description='Schedule something comforting - favorite meal, relaxing activity, or rest time',
            priority='medium',
            confidence=0.85,
            rationale='Self-care and comfort can help improve your mood.'
        ))
        
        return responses
    
    def _anxiety_responses(self, detection: EmotionDetection) -> List[EmotionResponse]:
        """Responses for anxious/confused users."""
        responses = []
        
        self.response_counter += 1
        responses.append(EmotionResponse(
            category='calendar_adjustment',
            action='create_structure',
            description='Let\'s break down your day into clear, manageable chunks',
            priority='high',
            confidence=0.92,
            rationale='Structure and clarity can reduce anxiety.'
        ))
        
        self.response_counter += 1
        responses.append(EmotionResponse(
            category='activity',
            action='grounding_exercise',
            description='Try a grounding exercise: 5-4-3-2-1 sensory awareness or deep breathing',
            priority='medium',
            confidence=0.90,
            rationale='Grounding techniques can help manage anxiety right now.'
        ))
        
        return responses
    
    def apply_stress_relief(self, events: List[Dict[str, Any]],
                          detection: EmotionDetection) -> Dict[str, Any]:
        """
        Apply calendar adjustments for stress relief.
        
        Args:
            events: Current calendar events
            detection: Emotion detection result
            
        Returns:
            Dictionary with suggested calendar changes
        """
        action_plan = {
            'stress_level': detection.stress_level.value,
            'actions': [],
            'rationale': 'Based on your current stress level'
        }
        
        if detection.stress_level in [StressLevel.HIGH, StressLevel.CRITICAL]:
            # Suggest rescheduling lower-priority items
            lower_priority = [e for e in events if e.get('priority') in ['low', 'optional']]
            
            if lower_priority:
                action_plan['actions'].append({
                    'type': 'reschedule',
                    'count': len(lower_priority),
                    'description': f'Reschedule {len(lower_priority)} lower-priority items to reduce load',
                    'items': [e.get('title', 'Event') for e in lower_priority[:3]]
                })
            
            # Suggest adding buffer time
            action_plan['actions'].append({
                'type': 'add_buffers',
                'description': 'Add 15-minute buffers between meetings for breathing room',
                'impact': 'Reduces back-to-back pressure'
            })
            
            # Suggest focus/break block
            action_plan['actions'].append({
                'type': 'add_break',
                'description': 'Add a 30-minute break block to decompress',
                'suggested_time': 'Mid-day or before your most stressful meeting'
            })
        
        return action_plan
