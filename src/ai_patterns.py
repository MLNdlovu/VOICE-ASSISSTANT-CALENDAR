"""
AI Patterns & Predictions Module

Detects behavioral patterns in calendar events and predicts user needs before they ask.
Analyzes: busy time patterns, event proximity, reminder preferences, focus patterns, etc.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional, Any
import json
import re

try:
    import openai
except ImportError:
    openai = None


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class TimeBlock:
    """Represents a time block in the calendar."""
    day_of_week: str  # 'Monday', 'Tuesday', etc.
    start_hour: int
    end_hour: int
    event_count: int = 0
    total_minutes: int = 0
    
    def __str__(self):
        return f"{self.day_of_week} {self.start_hour:02d}:00-{self.end_hour:02d}:00"


@dataclass
class Pattern:
    """Represents a detected pattern."""
    name: str
    confidence: float  # 0.0-1.0
    description: str
    supporting_evidence: List[str] = field(default_factory=list)
    frequency: str = "regular"  # rare, occasional, regular, frequent
    
    def __str__(self):
        confidence_pct = int(self.confidence * 100)
        return f"[{confidence_pct}%] {self.name}: {self.description}"


@dataclass
class Prediction:
    """Represents a prediction about user needs."""
    prediction_id: str
    category: str  # 'learning_blocks', 'travel_time', 'reminder', 'focus_time', 'break', 'team_pattern'
    insight: str
    recommendation: str
    actionable: bool
    priority: str  # low, medium, high
    confidence: float
    
    def to_dict(self):
        return {
            "id": self.prediction_id,
            "category": self.category,
            "insight": self.insight,
            "recommendation": self.recommendation,
            "actionable": self.actionable,
            "priority": self.priority,
            "confidence": int(self.confidence * 100),
        }


# ============================================================================
# Analyzers
# ============================================================================

class BusyTimeAnalyzer:
    """Analyzes when the user is consistently busy."""
    
    def __init__(self):
        self.time_blocks = defaultdict(lambda: {
            'count': 0,
            'total_minutes': 0,
            'events': []
        })
    
    def analyze(self, events: List[Dict[str, Any]]) -> Tuple[List[TimeBlock], List[Pattern]]:
        """
        Analyze busy time patterns.
        
        Args:
            events: List of calendar events with start_time, end_time, title
            
        Returns:
            (busy_blocks, patterns)
        """
        self.time_blocks.clear()
        patterns = []
        
        if not events:
            return [], patterns
        
        # Group events by day and hour
        for event in events:
            if 'start_time' not in event or 'end_time' not in event:
                continue
                
            try:
                start = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(event['end_time'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                continue
            
            day_name = start.strftime('%A')
            start_hour = start.hour
            end_hour = end.hour if end.hour > start.hour else start.hour + 1
            
            # Track each hour block
            for hour in range(start_hour, end_hour):
                block_key = (day_name, hour)
                self.time_blocks[block_key]['count'] += 1
                minutes = (min(end.hour, hour + 1) - max(start.hour, hour)) * 60
                self.time_blocks[block_key]['total_minutes'] += minutes
                self.time_blocks[block_key]['events'].append(event.get('title', 'Event'))
        
        # Find consistently busy blocks (appearing in 3+ events)
        busy_blocks = []
        for (day, hour), data in sorted(self.time_blocks.items()):
            if data['count'] >= 3:
                block = TimeBlock(
                    day_of_week=day,
                    start_hour=hour,
                    end_hour=hour + 1,
                    event_count=data['count'],
                    total_minutes=data['total_minutes']
                )
                busy_blocks.append(block)
        
        # Generate patterns
        if busy_blocks:
            # Group by day
            days_busy = Counter(b.day_of_week for b in busy_blocks)
            if days_busy:
                busiest_day = days_busy.most_common(1)[0]
                count = len([b for b in busy_blocks if b.day_of_week == busiest_day[0]])
                patterns.append(Pattern(
                    name="Consistent Tuesday Mornings",
                    confidence=min(1.0, count / 4),
                    description=f"You're busy every {busiest_day[0].lower()} morning — {count} recurring time slots",
                    supporting_evidence=[str(b) for b in busy_blocks if b.day_of_week == busiest_day[0]],
                    frequency="frequent" if count >= 3 else "regular"
                ))
        
        return busy_blocks, patterns


class EventProximityAnalyzer:
    """Detects events scheduled too close together."""
    
    def __init__(self, min_gap_minutes: int = 15):
        self.min_gap_minutes = min_gap_minutes
    
    def analyze(self, events: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Pattern]]:
        """
        Detect events scheduled with insufficient travel time.
        
        Args:
            events: List of events with start_time, end_time, title
            
        Returns:
            (close_pairs, patterns)
        """
        close_pairs = []
        patterns = []
        
        if not events or len(events) < 2:
            return close_pairs, patterns
        
        # Sort by start time
        sorted_events = []
        for event in events:
            try:
                start = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
                sorted_events.append((start, event))
            except (ValueError, AttributeError):
                continue
        
        sorted_events.sort(key=lambda x: x[0])
        
        # Find close pairs
        for i in range(len(sorted_events) - 1):
            current_end = datetime.fromisoformat(
                sorted_events[i][1]['end_time'].replace('Z', '+00:00')
            )
            next_start = sorted_events[i + 1][0]
            
            gap = (next_start - current_end).total_seconds() / 60
            
            if gap < self.min_gap_minutes and gap >= 0:
                close_pairs.append({
                    'event1': sorted_events[i][1],
                    'event2': sorted_events[i + 1][1],
                    'gap_minutes': int(gap)
                })
        
        # Generate patterns
        if close_pairs:
            patterns.append(Pattern(
                name="Travel Time Conflicts",
                confidence=min(1.0, len(close_pairs) / 5),
                description=f"You booked {len(close_pairs)} events with minimal gaps (< {self.min_gap_minutes} min)",
                supporting_evidence=[f"{p['event1'].get('title', 'Event1')} → {p['event2'].get('title', 'Event2')} ({p['gap_minutes']} min gap)" for p in close_pairs[:3]],
                frequency="frequent" if len(close_pairs) >= 3 else "occasional"
            ))
        
        return close_pairs, patterns


class ReminderPatternAnalyzer:
    """Detects reminder and notification preferences."""
    
    def __init__(self):
        self.reminders = defaultdict(int)
        self.no_show_times = []
    
    def analyze(self, events: List[Dict[str, Any]]) -> Tuple[Dict, List[Pattern]]:
        """
        Analyze reminder needs based on event types.
        
        Args:
            events: List of events with titles, times, reminder data
            
        Returns:
            (reminder_stats, patterns)
        """
        patterns = []
        early_events = 0
        missed_early = 0
        
        for event in events:
            try:
                start = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
                
                # Count very early events (before 9am)
                if start.hour < 9:
                    early_events += 1
                    # Heuristic: if early event has no reminder, user might forget
                    if 'reminder' not in event or not event.get('reminder'):
                        missed_early += 1
            except (ValueError, AttributeError):
                continue
        
        # Generate patterns
        if early_events > 3 and missed_early > early_events * 0.5:
            patterns.append(Pattern(
                name="Early Morning Reminders Needed",
                confidence=min(1.0, missed_early / early_events),
                description=f"You tend to forget early events — {early_events} early bookings with {missed_early} without reminders",
                supporting_evidence=[f"Detected {early_events} events before 9am", f"{missed_early} lacked reminder settings"],
                frequency="regular"
            ))
        
        return {'early_events': early_events}, patterns


class FocusTimeAnalyzer:
    """Detects opportunities and needs for focus/deep work time."""
    
    def analyze(self, events: List[Dict[str, Any]]) -> Tuple[Dict, List[Pattern]]:
        """
        Analyze focus time availability.
        
        Args:
            events: List of events
            
        Returns:
            (focus_stats, patterns)
        """
        patterns = []
        total_minutes = 60 * 24 * 7  # Assume weekly analysis
        event_minutes = 0
        
        for event in events:
            try:
                start = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(event['end_time'].replace('Z', '+00:00'))
                event_minutes += (end - start).total_seconds() / 60
            except (ValueError, AttributeError):
                continue
        
        focus_available = total_minutes - event_minutes
        focus_pct = focus_available / total_minutes
        
        if focus_pct < 0.2:  # Less than 20% free time
            patterns.append(Pattern(
                name="Limited Focus Time",
                confidence=0.85,
                description=f"Your calendar is packed — only {int(focus_pct * 100)}% free time for deep work",
                supporting_evidence=[f"Total meeting time: {int(event_minutes)} minutes", f"Available: {int(focus_available)} minutes"],
                frequency="frequent"
            ))
        elif focus_pct > 0.5:
            patterns.append(Pattern(
                name="Abundant Focus Time",
                confidence=0.9,
                description=f"You've got plenty of unscheduled time — {int(focus_pct * 100)}% of your week is free",
                supporting_evidence=[f"Great for deep work and learning blocks"],
                frequency="regular"
            ))
        
        return {'focus_available_pct': focus_pct, 'event_minutes': event_minutes}, patterns


class BreakPatternAnalyzer:
    """Detects when the user is overworking without breaks."""
    
    def analyze(self, events: List[Dict[str, Any]]) -> Tuple[Dict, List[Pattern]]:
        """
        Analyze break patterns.
        
        Args:
            events: List of events
            
        Returns:
            (break_stats, patterns)
        """
        patterns = []
        back_to_back_sequences = 0
        current_sequence = 0
        
        sorted_events = []
        for event in events:
            try:
                start = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
                sorted_events.append((start, event))
            except (ValueError, AttributeError):
                continue
        
        sorted_events.sort(key=lambda x: x[0])
        
        for i in range(len(sorted_events) - 1):
            current_end = datetime.fromisoformat(sorted_events[i][1]['end_time'].replace('Z', '+00:00'))
            next_start = sorted_events[i + 1][0]
            gap = (next_start - current_end).total_seconds() / 60
            
            if gap < 10:  # Less than 10 minutes between events
                current_sequence += 1
                if current_sequence > 2:
                    back_to_back_sequences += 1
            else:
                current_sequence = 0
        
        if back_to_back_sequences > 0:
            patterns.append(Pattern(
                name="Lack of Break Time",
                confidence=min(1.0, back_to_back_sequences / 3),
                description=f"You have {back_to_back_sequences} sequences of back-to-back events with no breaks",
                supporting_evidence=["Consider adding 15-30 min buffer time between meetings"],
                frequency="regular" if back_to_back_sequences >= 2 else "occasional"
            ))
        
        return {'back_to_back_sequences': back_to_back_sequences}, patterns


# ============================================================================
# Insight Generation & Prediction
# ============================================================================

class AIInsightGenerator:
    """Generates actionable AI insights from patterns."""
    
    def __init__(self, use_gpt: bool = False):
        self.use_gpt = use_gpt and openai is not None
        self.prediction_counter = 0
    
    def generate_insights(self, patterns: List[Pattern], events: List[Dict]) -> List[Prediction]:
        """
        Convert patterns into actionable predictions.
        
        Args:
            patterns: List of detected patterns
            events: Original event list
            
        Returns:
            List of predictions
        """
        predictions = []
        
        for pattern in patterns:
            if "Consistent" in pattern.name and "Morning" in pattern.name:
                pred = self._create_learning_block_prediction(pattern)
                predictions.append(pred)
            
            elif "Travel Time" in pattern.name:
                pred = self._create_travel_time_prediction(pattern)
                predictions.append(pred)
            
            elif "Early Morning" in pattern.name:
                pred = self._create_reminder_prediction(pattern)
                predictions.append(pred)
            
            elif "Limited Focus" in pattern.name:
                pred = self._create_focus_time_prediction(pattern)
                predictions.append(pred)
            
            elif "Lack of Break" in pattern.name:
                pred = self._create_break_prediction(pattern)
                predictions.append(pred)
            
            elif "Abundant Focus" in pattern.name:
                pred = self._create_learning_opportunity_prediction(pattern)
                predictions.append(pred)
        
        # Enhance with GPT if available
        if self.use_gpt:
            predictions = self._enhance_with_gpt(predictions)
        
        return predictions
    
    def _create_learning_block_prediction(self, pattern: Pattern) -> Prediction:
        """Create learning block suggestion."""
        self.prediction_counter += 1
        return Prediction(
            prediction_id=f"pred_{self.prediction_counter}",
            category="learning_blocks",
            insight=pattern.description,
            recommendation="Block these consistent busy slots for focused learning — they're already protected time anyway",
            actionable=True,
            priority="high" if pattern.confidence > 0.8 else "medium",
            confidence=pattern.confidence
        )
    
    def _create_travel_time_prediction(self, pattern: Pattern) -> Prediction:
        """Create travel time suggestion."""
        self.prediction_counter += 1
        return Prediction(
            prediction_id=f"pred_{self.prediction_counter}",
            category="travel_time",
            insight=pattern.description,
            recommendation="Auto-add 15-30 minute travel buffers between back-to-back events",
            actionable=True,
            priority="high",
            confidence=pattern.confidence
        )
    
    def _create_reminder_prediction(self, pattern: Pattern) -> Prediction:
        """Create early reminder suggestion."""
        self.prediction_counter += 1
        return Prediction(
            prediction_id=f"pred_{self.prediction_counter}",
            category="reminder",
            insight=pattern.description,
            recommendation="Enable 10-minute earlier reminders for all morning events (before 9am)",
            actionable=True,
            priority="high" if pattern.confidence > 0.7 else "medium",
            confidence=pattern.confidence
        )
    
    def _create_focus_time_prediction(self, pattern: Pattern) -> Prediction:
        """Create focus time suggestion."""
        self.prediction_counter += 1
        return Prediction(
            prediction_id=f"pred_{self.prediction_counter}",
            category="focus_time",
            insight=pattern.description,
            recommendation="Block 2-3 hours weekly for deep work — consider Friday afternoons or early mornings",
            actionable=True,
            priority="medium",
            confidence=pattern.confidence
        )
    
    def _create_break_prediction(self, pattern: Pattern) -> Prediction:
        """Create break time suggestion."""
        self.prediction_counter += 1
        return Prediction(
            prediction_id=f"pred_{self.prediction_counter}",
            category="break",
            insight=pattern.description,
            recommendation="Schedule 15-30 minute breaks between meetings to recharge and prevent burnout",
            actionable=True,
            priority="high",
            confidence=pattern.confidence
        )
    
    def _create_learning_opportunity_prediction(self, pattern: Pattern) -> Prediction:
        """Create learning opportunity suggestion."""
        self.prediction_counter += 1
        return Prediction(
            prediction_id=f"pred_{self.prediction_counter}",
            category="learning_blocks",
            insight=pattern.description,
            recommendation="Use your abundant free time for skill development — consider booking learning sessions",
            actionable=True,
            priority="low",
            confidence=pattern.confidence
        )
    
    def _enhance_with_gpt(self, predictions: List[Prediction]) -> List[Prediction]:
        """Enhance predictions with GPT-powered insights."""
        try:
            for pred in predictions:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{
                        "role": "user",
                        "content": f"Enhance this calendar insight with a friendly, actionable recommendation:\n{pred.insight}\n\nCurrent recommendation: {pred.recommendation}\n\nProvide a more personalized and concise version."
                    }],
                    max_tokens=100,
                    temperature=0.7
                )
                pred.recommendation = response['choices'][0]['message']['content'].strip()
            return predictions
        except Exception:
            # Fallback: return original predictions
            return predictions


# ============================================================================
# Main Service
# ============================================================================

class PatternPredictionService:
    """Main service orchestrating all pattern detection and prediction."""
    
    def __init__(self, use_gpt: bool = False, min_gap_minutes: int = 15):
        self.busy_analyzer = BusyTimeAnalyzer()
        self.proximity_analyzer = EventProximityAnalyzer(min_gap_minutes=min_gap_minutes)
        self.reminder_analyzer = ReminderPatternAnalyzer()
        self.focus_analyzer = FocusTimeAnalyzer()
        self.break_analyzer = BreakPatternAnalyzer()
        self.insight_generator = AIInsightGenerator(use_gpt=use_gpt)
        self.use_gpt = use_gpt
    
    def analyze_calendar(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform comprehensive analysis on calendar events.
        
        Args:
            events: List of calendar events
            
        Returns:
            Comprehensive analysis including patterns and predictions
        """
        all_patterns = []
        
        # Run all analyzers
        busy_blocks, busy_patterns = self.busy_analyzer.analyze(events)
        all_patterns.extend(busy_patterns)
        
        close_pairs, proximity_patterns = self.proximity_analyzer.analyze(events)
        all_patterns.extend(proximity_patterns)
        
        reminder_stats, reminder_patterns = self.reminder_analyzer.analyze(events)
        all_patterns.extend(reminder_patterns)
        
        focus_stats, focus_patterns = self.focus_analyzer.analyze(events)
        all_patterns.extend(focus_patterns)
        
        break_stats, break_patterns = self.break_analyzer.analyze(events)
        all_patterns.extend(break_patterns)
        
        # Generate predictions from patterns
        predictions = self.insight_generator.generate_insights(all_patterns, events)
        
        # Sort predictions by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        predictions.sort(key=lambda p: (priority_order.get(p.priority, 3), -p.confidence))
        
        return {
            'event_count': len(events),
            'patterns': [{'name': p.name, 'confidence': int(p.confidence * 100), 'description': p.description, 'frequency': p.frequency} for p in all_patterns],
            'predictions': [p.to_dict() for p in predictions],
            'summary': self._generate_summary(all_patterns, predictions),
            'generated_at': datetime.now().isoformat()
        }
    
    def _generate_summary(self, patterns: List[Pattern], predictions: List[Prediction]) -> str:
        """Generate a natural language summary of findings."""
        if not patterns:
            return "No significant patterns detected in your calendar."
        
        high_confidence = [p for p in patterns if p.confidence > 0.8]
        if not high_confidence:
            return f"Detected {len(patterns)} calendar patterns. Review predictions for suggestions."
        
        top_pattern = high_confidence[0]
        return f"Strong pattern detected: {top_pattern.description} | {len(predictions)} actionable insights available."
    
    def get_prediction_by_id(self, predictions: List[Prediction], pred_id: str) -> Optional[Prediction]:
        """Retrieve a specific prediction."""
        for pred in predictions:
            if pred.prediction_id == pred_id:
                return pred
        return None
    
    def apply_prediction(self, prediction: Prediction, events: List[Dict]) -> Dict[str, Any]:
        """
        Apply a prediction recommendation to calendar.
        
        Args:
            prediction: The prediction to apply
            events: Current events
            
        Returns:
            Modified events or action plan
        """
        action_plan = {
            'prediction_id': prediction.prediction_id,
            'category': prediction.category,
            'actions': [],
            'status': 'ready'
        }
        
        if prediction.category == 'learning_blocks':
            action_plan['actions'].append({
                'type': 'block_time',
                'description': 'Block consistent busy slots for learning',
                'examples': ['Tuesday mornings 10-12', 'Thursday afternoons 2-4']
            })
        
        elif prediction.category == 'travel_time':
            action_plan['actions'].append({
                'type': 'add_buffers',
                'description': 'Add 15-30 min buffers between events',
                'affected_events': len(events)
            })
        
        elif prediction.category == 'reminder':
            action_plan['actions'].append({
                'type': 'enable_reminders',
                'description': 'Add 10-minute early reminders to morning events',
                'affected_events': sum(1 for e in events if datetime.fromisoformat(e.get('start_time', '').replace('Z', '+00:00')).hour < 9 if 'start_time' in e)
            })
        
        elif prediction.category == 'focus_time':
            action_plan['actions'].append({
                'type': 'block_focus',
                'description': 'Add 2-3 hour deep work blocks weekly',
                'suggestions': ['Friday afternoon 2-5pm', 'Monday morning 9-11am']
            })
        
        elif prediction.category == 'break':
            action_plan['actions'].append({
                'type': 'add_breaks',
                'description': 'Insert 15-30 min breaks between back-to-back events',
                'affected_events': len(events)
            })
        
        return action_plan
