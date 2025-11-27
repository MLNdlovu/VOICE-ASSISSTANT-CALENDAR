"""
Scheduler Handler for Voice Assistant Calendar

Integrates AI Smart Scheduler with voice commands, web endpoints,
and dashboard rendering.

NOTE: This module has been simplified for web-first architecture.
Optional AI features (SmartScheduler, sentiment analysis, etc.) are disabled.
"""

import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from flask import session

from src.nlu import parse_natural_language_event

# Optional AI features - safely disabled for web deployment
SmartScheduler = None
SchedulePreferences = None
AgendaSummaryService = None
AgendaEvent = None
PatternPredictionService = None
EventEmailDrafter = None
EmailService = None
EmailTone = None
EmailType = None
VoiceSentimentAnalyzer = None
EmotionResponseEngine = None
EmotionDetection = None
TaskExtractor = None
JarvisConversationManager = None
DialogueType = None
VisualCalendarAnalyzer = None
CalendarHeatmap = None
AccessibilityManager = None
SpeechRate = None
AccessibilityMode = None

try:
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    HAS_GOOGLE_API = True
except ImportError:
    HAS_GOOGLE_API = False


class SchedulerCommandHandler:
    """Handles voice commands and web requests for smart scheduling."""

    def __init__(self, google_credentials_path: Optional[str] = None):
        """Initialize the scheduler handler."""
        self.google_credentials_path = google_credentials_path or '.config/credentials.json'
        self.scheduler = None
        self.agenda_service = None
        self.calendar_service = None
        self.pattern_service = None
        self.email_service = None
        self.sentiment_analyzer = None
        self.emotion_engine = None
        self.task_extractor = None
        self.conversation_manager = None
        self.visual_calendar = None
        self.accessibility_manager = None
        self._init_scheduler()
        self._init_agenda()
        self._init_patterns()
        self._init_email_service()
        self._init_sentiment_analyzer()
        self._init_task_extraction()
        self._init_conversation_manager()
        self._init_visual_calendar()
        self._init_accessibility()

    def _init_scheduler(self):
        """Initialize SmartScheduler with user preferences."""
        try:
            # Default preferences: avoid mornings and weekends
            preferences = SchedulePreferences(
                avoid_times=['morning', 'weekend'],
                preferred_times=['afternoon'],
                work_hours_only=True,
                earliest_hour=9,
                latest_hour=17
            )
            self.scheduler = SmartScheduler(
                google_credentials_path=self.google_credentials_path,
                preferences=preferences
            )
        except Exception as e:
            print(f"[WARN] Could not initialize SmartScheduler: {e}")
            self.scheduler = None

    def _init_agenda(self):
        """Initialize agenda summary service."""
        try:
            self.agenda_service = AgendaSummaryService(use_gpt=True)
        except Exception as e:
            print(f"[WARN] Could not initialize Agenda Service: {e}")
            self.agenda_service = None

    def _init_patterns(self):
        """Initialize pattern prediction service."""
        try:
            self.pattern_service = PatternPredictionService(use_gpt=True, min_gap_minutes=15)
        except Exception as e:
            print(f"[WARN] Could not initialize Pattern Service: {e}")
            self.pattern_service = None

    def _init_email_service(self):
        """Initialize email drafting service."""
        try:
            email_drafter = EventEmailDrafter(use_gpt=True)
            self.email_service = EmailService(email_drafter)
        except Exception as e:
            print(f"[WARN] Could not initialize Email Service: {e}")
            self.email_service = None

    def _init_sentiment_analyzer(self):
        """Initialize voice sentiment analysis."""
        try:
            self.sentiment_analyzer = VoiceSentimentAnalyzer(use_transformers=True)
            self.emotion_engine = EmotionResponseEngine()
        except Exception as e:
            print(f"[WARN] Could not initialize Sentiment Analyzer: {e}")
            self.sentiment_analyzer = None
            self.emotion_engine = None

    def _init_task_extraction(self):
        """Initialize task extraction service."""
        try:
            self.task_extractor = TaskExtractor(use_gpt=True)
        except Exception as e:
            print(f"[WARN] Could not initialize Task Extractor: {e}")
            self.task_extractor = None

    def _init_conversation_manager(self):
        """Initialize Jarvis-style conversation manager."""
        try:
            self.conversation_manager = JarvisConversationManager(use_gpt=True)
        except Exception as e:
            print(f"[WARN] Could not initialize Conversation Manager: {e}")
            self.conversation_manager = None

    def _init_visual_calendar(self):
        """Initialize visual calendar analyzer."""
        try:
            self.visual_calendar = VisualCalendarAnalyzer(use_gpt=True)
        except Exception as e:
            print(f"[WARN] Could not initialize Visual Calendar: {e}")
            self.visual_calendar = None

    def _init_accessibility(self):
        """Initialize accessibility manager."""
        try:
            self.accessibility_manager = AccessibilityManager()
        except Exception as e:
            print(f"[WARN] Could not initialize Accessibility Manager: {e}")
            self.accessibility_manager = None

    def handle_find_best_time(self, command_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle 'find-best-time' voice command.
        
        Expected params:
        - event_description: str (e.g., "2-hour session")
        - duration_minutes: int
        - search_window_days: int
        
        Returns: Dict with recommendations
        """
        if not self.scheduler:
            return {
                'status': 'error',
                'message': 'Scheduler not initialized. Check Google Calendar credentials.'
            }

        try:
            event_desc = command_params.get('event_description', 'Meeting')
            duration = command_params.get('duration_minutes', 60)
            window = command_params.get('search_window_days', 7)

            results = self.scheduler.find_best_times(
                event_description=event_desc,
                duration_minutes=duration,
                search_window_days=window,
                top_n=3
            )

            return results

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def handle_smart_booking_with_nlu(self, user_text: str) -> Dict[str, Any]:
        """
        Handle messy natural language booking requests.
        Uses NLU parser to extract event details, then finds best times.
        
        Args:
            user_text: Raw voice input (e.g., "Find the best time for a 2-hour session next week")
        
        Returns:
            Dict with parsed event and recommendations
        """
        if not self.scheduler:
            return {
                'status': 'error',
                'message': 'Scheduler not available'
            }

        try:
            # Parse using NLU module
            parsed = parse_natural_language_event(user_text)

            # Extract duration
            duration_minutes = 60
            if parsed.get('duration'):
                duration_minutes = int(parsed['duration'].total_seconds() / 60)

            # Extract event title
            event_title = parsed.get('title', 'Meeting')

            # Extract search window (if recurrence suggests "this week")
            search_window = 7
            if parsed.get('recurrence') and parsed['recurrence'].get('freq') == 'daily':
                search_window = 7

            # Find best times
            results = self.scheduler.find_best_times(
                event_description=event_title,
                duration_minutes=duration_minutes,
                search_window_days=search_window,
                top_n=3
            )

            # Merge NLU parsed info with recommendations
            results['parsed_event'] = {
                'title': event_title,
                'duration_minutes': duration_minutes,
                'time_window': parsed.get('time_window'),
                'avoid_early': parsed.get('avoid_early', False),
                'relative_anchor': parsed.get('relative')
            }

            return results

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error parsing event: {str(e)}'
            }

    def format_recommendations_for_voice(self, results: Dict[str, Any]) -> str:
        """
        Format scheduling recommendations as natural speech.
        
        Args:
            results: Recommendation dict from find_best_times
        
        Returns:
            Formatted voice response string
        """
        if results.get('status') == 'error':
            return f"I couldn't find available times: {results.get('message', 'Unknown error')}"

        if results.get('status') == 'no_slots_found':
            return f"I couldn't find any available {results.get('duration_minutes', 60)}-minute slots in the next {results.get('search_window', {}).get('end', 'week')}. Would you like me to expand the search?"

        recommendations = results.get('recommendations', [])
        if not recommendations:
            return "No recommendations found. Please check your calendar and try again."

        # Format top 3 recommendations
        response = f"I found some good times for your {results.get('event', 'meeting')}. "
        
        for i, rec in enumerate(recommendations[:3], 1):
            try:
                if isinstance(rec, dict):
                    start_time = rec.get('start')
                    if isinstance(start_time, str):
                        dt = datetime.fromisoformat(start_time)
                        time_str = dt.strftime('%A at %I:%M %p')
                        reason = rec.get('reason', '')
                        response += f"Option {i}: {time_str}"
                        if reason:
                            response += f" ({reason})"
                        response += ". "
            except Exception as e:
                print(f"Error formatting recommendation {i}: {e}")
                continue

        response += "Would you like me to book one of these times?"
        return response

    def format_recommendations_for_dashboard(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format recommendations for web dashboard display.
        
        Returns:
            Dict with formatted times and UI-friendly data
        """
        if results.get('status') != 'success':
            return {
                'error': True,
                'message': results.get('message', 'Unknown error'),
                'status': results.get('status', 'error')
            }

        recommendations = results.get('recommendations', [])
        formatted = {
            'event': results.get('event', 'Meeting'),
            'duration_minutes': results.get('duration_minutes', 60),
            'total_slots': results.get('total_available_slots', 0),
            'recommendations': [],
            'parsed_event': results.get('parsed_event')
        }

        for rec in recommendations[:5]:  # Show top 5
            try:
                if isinstance(rec, dict):
                    start_time = rec.get('start')
                    end_time = rec.get('end')
                    
                    if isinstance(start_time, str):
                        start_dt = datetime.fromisoformat(start_time)
                        end_dt = datetime.fromisoformat(end_time) if end_time else start_dt
                    else:
                        start_dt = start_time
                        end_dt = end_time or start_time

                    formatted['recommendations'].append({
                        'start': start_dt.isoformat(),
                        'end': end_dt.isoformat(),
                        'display': start_dt.strftime('%A, %B %d at %I:%M %p'),
                        'reason': rec.get('reason', 'Available'),
                        'datetime_obj': start_dt
                    })
            except Exception as e:
                print(f"Error formatting dashboard recommendation: {e}")
                continue

        # Sort by datetime
        formatted['recommendations'] = sorted(
            formatted['recommendations'],
            key=lambda x: x['datetime_obj']
        )

        return formatted

    def handle_agenda_summary(self, command_params: Dict[str, Any], calendar_events: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Handle 'agenda-summary' voice command.
        
        Expected params:
        - period: 'day', 'week', or 'month'
        - use_gpt: bool (whether to use AI enhancement)
        
        Optional:
        - calendar_events: Pre-fetched calendar events (Google format)
        
        Returns: Dict with summary and details
        """
        if not self.agenda_service:
            return {
                'status': 'error',
                'message': 'Agenda service not initialized'
            }

        try:
            period = command_params.get('period', 'day')
            use_gpt = command_params.get('use_gpt', False)

            # Convert calendar events to AgendaEvent objects
            events = self._convert_calendar_events(calendar_events or [])

            # Generate summary
            if period == 'day':
                summary = self.agenda_service.get_today_summary(events, use_gpt=use_gpt)
            elif period == 'week':
                summary = self.agenda_service.get_week_summary(events, use_gpt=use_gpt)
            else:
                summary = self.agenda_service.get_week_summary(events, use_gpt=use_gpt)

            result = self.agenda_service.get_summary_with_details(events, period=period)
            result['summary'] = summary

            return {
                'status': 'success',
                'summary': summary,
                'period': period,
                'metrics': result.get('metrics', {}),
                'event_count': len(events)
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def _convert_calendar_events(self, google_events: List[Dict]) -> List[AgendaEvent]:
        """Convert Google Calendar events to AgendaEvent objects."""
        agenda_events = []
        
        for event in google_events:
            try:
                title = event.get('summary', 'Untitled')
                description = event.get('description', '')
                
                # Parse start/end times
                start_str = event.get('start', {}).get('dateTime') or event.get('start', {}).get('date')
                end_str = event.get('end', {}).get('dateTime') or event.get('end', {}).get('date')
                
                if not start_str or not end_str:
                    continue

                # Parse ISO datetime
                try:
                    if 'T' in start_str:
                        start = datetime.fromisoformat(start_str.replace('Z', '+00:00')).astimezone().replace(tzinfo=None)
                        end = datetime.fromisoformat(end_str.replace('Z', '+00:00')).astimezone().replace(tzinfo=None)
                    else:
                        start = datetime.fromisoformat(start_str)
                        end = datetime.fromisoformat(end_str)
                except Exception:
                    continue

                duration = int((end - start).total_seconds() / 60)
                
                agenda_event = AgendaEvent(
                    title=title,
                    start=start,
                    end=end,
                    duration_minutes=duration,
                    description=description
                )
                agenda_events.append(agenda_event)

            except Exception as e:
                print(f"Error converting calendar event: {e}")
                continue

        return agenda_events

    def format_summary_for_voice(self, result: Dict[str, Any]) -> str:
        """Format agenda summary for voice output."""
        if result.get('status') == 'error':
            return f"I couldn't generate your summary: {result.get('message', 'Unknown error')}"

        return result.get('summary', 'No summary available')

    def format_summary_for_dashboard(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format agenda summary for web dashboard."""
        if result.get('status') != 'success':
            return {
                'error': True,
                'message': result.get('message', 'Unknown error'),
                'status': result.get('status', 'error')
            }

        return {
            'summary': result.get('summary', ''),
            'period': result.get('period', 'day'),
            'event_count': result.get('event_count', 0),
            'metrics': result.get('metrics', {}),
            'error': False
        }

    def handle_predict_patterns(self, command_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle pattern prediction request.
        
        Args:
            command_params: Dict with optional 'calendar_events' key
            
        Returns:
            Dict with patterns, predictions, and summary
        """
        if not self.pattern_service:
            return {
                'status': 'error',
                'message': 'Pattern service not initialized'
            }

        try:
            # Get calendar events from params or fetch from Google
            events = command_params.get('calendar_events', [])
            
            if not events and self.scheduler and hasattr(self.scheduler, 'calendar_helper'):
                try:
                    events = self.scheduler.calendar_helper.get_events(days_ahead=30)
                except Exception:
                    pass
            
            if not events:
                return {
                    'status': 'warning',
                    'message': 'No calendar events available for analysis',
                    'patterns': [],
                    'predictions': []
                }

            # Analyze calendar
            analysis = self.pattern_service.analyze_calendar(events)
            
            return {
                'status': 'success',
                'event_count': analysis['event_count'],
                'patterns': analysis['patterns'],
                'predictions': analysis['predictions'],
                'summary': analysis['summary'],
                'generated_at': analysis['generated_at']
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def handle_apply_prediction(self, command_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a specific prediction/recommendation.
        
        Args:
            command_params: Dict with 'prediction_id' and optionally 'calendar_events'
            
        Returns:
            Dict with action plan for applying prediction
        """
        if not self.pattern_service:
            return {
                'status': 'error',
                'message': 'Pattern service not initialized'
            }

        try:
            prediction_id = command_params.get('prediction_id')
            events = command_params.get('calendar_events', [])
            
            if not prediction_id:
                return {
                    'status': 'error',
                    'message': 'prediction_id is required'
                }

            # Get predictions from analysis
            analysis = self.pattern_service.analyze_calendar(events)
            predictions = analysis.get('predictions', [])
            
            # Find the specific prediction
            target_pred = None
            for pred_dict in predictions:
                if pred_dict.get('id') == prediction_id:
                    target_pred = pred_dict
                    break
            
            if not target_pred:
                return {
                    'status': 'error',
                    'message': f'Prediction {prediction_id} not found'
                }

            return {
                'status': 'success',
                'prediction_id': prediction_id,
                'category': target_pred.get('category'),
                'insight': target_pred.get('insight'),
                'recommendation': target_pred.get('recommendation'),
                'action_plan': {
                    'type': target_pred.get('category'),
                    'steps': self._get_action_steps(target_pred.get('category'), events)
                }
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def handle_draft_email(self, command_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle email drafting request.
        
        Args:
            command_params: Dict with 'event', 'recipient', 'email_type', 'tone'
            
        Returns:
            Dict with drafted email
        """
        if not self.email_service:
            return {
                'status': 'error',
                'message': 'Email service not initialized'
            }

        try:
            event = command_params.get('event')
            recipient = command_params.get('recipient', 'Team')
            email_type = command_params.get('email_type', 'thank_you')
            tone = command_params.get('tone', 'professional')
            
            # Map string types/tones to enums
            type_map = {
                'thank_you': EmailType.THANK_YOU,
                'reminder': EmailType.REMINDER,
                'follow_up': EmailType.FOLLOW_UP,
                'cancellation': EmailType.CANCELLATION
            }
            tone_map = {
                'formal': EmailTone.FORMAL,
                'professional': EmailTone.PROFESSIONAL,
                'casual': EmailTone.CASUAL,
                'friendly': EmailTone.FRIENDLY,
                'grateful': EmailTone.GRATEFUL,
                'urgent': EmailTone.URGENT
            }
            
            email_type_enum = type_map.get(email_type.lower(), EmailType.THANK_YOU)
            tone_enum = tone_map.get(tone.lower(), EmailTone.PROFESSIONAL)
            
            # Draft email
            drafted = self.email_service.draft_email(
                event=event,
                email_type=email_type_enum,
                recipient=recipient,
                tone=tone_enum
            )
            
            return {
                'status': 'success',
                'draft_id': drafted.draft_id,
                'type': drafted.email_type.value,
                'tone': drafted.tone.value,
                'recipient': drafted.recipient,
                'subject': drafted.subject,
                'body': drafted.body,
                'event_title': drafted.event_title
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def handle_sentiment_analysis(self, command_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze emotion/sentiment from voice input.
        
        Args:
            command_params: Dict with 'text' (voice transcription)
            
        Returns:
            Dict with emotion detection and recommendations
        """
        if not self.sentiment_analyzer or not self.emotion_engine:
            return {
                'status': 'error',
                'message': 'Sentiment analyzer not initialized'
            }

        try:
            text = command_params.get('text', '')
            if not text:
                return {
                    'status': 'error',
                    'message': 'No text provided for analysis'
                }
            
            # Detect emotion
            emotion_detection = self.sentiment_analyzer.detect_emotion(text)
            
            # Generate responses
            responses = self.emotion_engine.get_responses(emotion_detection)
            
            return {
                'status': 'success',
                'emotion': emotion_detection.to_dict(),
                'summary': self.sentiment_analyzer.get_emotion_summary(emotion_detection),
                'recommendations': [
                    {
                        'category': r.category,
                        'action': r.action,
                        'description': r.description,
                        'priority': r.priority,
                        'confidence': r.confidence,
                        'rationale': r.rationale
                    } for r in responses
                ]
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def handle_mood_based_calendar_adjustment(self, command_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply mood-based calendar adjustments.
        
        Args:
            command_params: Dict with 'text' (command) and 'calendar_events'
            
        Returns:
            Dict with calendar adjustment plan
        """
        if not self.sentiment_analyzer or not self.emotion_engine:
            return {
                'status': 'error',
                'message': 'Sentiment analyzer not initialized'
            }

        try:
            text = command_params.get('text', '')
            events = command_params.get('calendar_events', [])
            
            if not text:
                return {
                    'status': 'error',
                    'message': 'No text provided'
                }
            
            # Detect emotion from command
            emotion_detection = self.sentiment_analyzer.detect_emotion(text)
            
            # Apply stress relief if stressed
            adjustment_plan = self.emotion_engine.apply_stress_relief(events, emotion_detection)
            
            return {
                'status': 'success',
                'emotion': emotion_detection.to_dict(),
                'mood': emotion_detection.mood.value,
                'stress_level': emotion_detection.stress_level.value,
                'adjustment_plan': adjustment_plan,
                'summary': self.sentiment_analyzer.get_emotion_summary(emotion_detection)
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def handle_task_extraction(self, command_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract tasks from conversational text.
        
        Args:
            command_params: Dict with 'text' (input text)
            
        Returns:
            Dict with extracted tasks
        """
        if not self.task_extractor:
            return {
                'status': 'error',
                'message': 'Task extractor not initialized'
            }

        try:
            text = command_params.get('text', '')
            
            if not text:
                return {
                    'status': 'error',
                    'message': 'No text provided'
                }
            
            # Extract tasks using both rule-based and GPT methods
            tasks = self.task_extractor.extract_tasks(text)
            
            # Extract entities
            entities = self.task_extractor.extract_entities(text)
            
            return {
                'status': 'success',
                'tasks': [
                    {
                        'id': t.id,
                        'type': t.type.value,
                        'title': t.title,
                        'description': t.description,
                        'deadline': t.deadline.isoformat() if t.deadline else None,
                        'priority': t.priority.value,
                        'status': t.status.value,
                        'confidence': t.confidence,
                        'entities': t.entities,
                        'reminder_before': t.reminder_before
                    } for t in tasks
                ],
                'entities': {
                    'people': entities.get('people', []),
                    'projects': entities.get('projects', []),
                    'dates': entities.get('dates', []),
                    'locations': entities.get('locations', [])
                },
                'summary': f"Extracted {len(tasks)} tasks with {len(entities.get('people', []))} people mentioned"
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def handle_conversation_turn(self, command_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a multi-turn conversation (Jarvis-style).
        
        Args:
            command_params: Dict with 'conversation_id', 'text' (user message),
                           optional: 'dialogue_type' ('scheduling', 'task_creation', etc.),
                           optional: 'required_fields'
            
        Returns:
            Dict with assistant response and conversation state
        """
        if not self.conversation_manager:
            return {
                'status': 'error',
                'message': 'Conversation manager not initialized'
            }

        try:
            conversation_id = command_params.get('conversation_id')
            user_text = command_params.get('text', '')
            
            if not conversation_id or not user_text:
                return {
                    'status': 'error',
                    'message': 'Conversation ID and user text required'
                }
            
            # Check if conversation exists; if not, create it
            if conversation_id not in self.conversation_manager.conversations:
                dialogue_type_str = command_params.get('dialogue_type', 'question_answer')
                required_fields = command_params.get('required_fields', [])
                
                # Map string to DialogueType enum
                dialogue_types = {
                    'qa': DialogueType.QUESTION_ANSWER,
                    'task_creation': DialogueType.TASK_CREATION,
                    'scheduling': DialogueType.SCHEDULING,
                    'clarification': DialogueType.CLARIFICATION,
                    'confirmation': DialogueType.CONFIRMATION,
                    'information': DialogueType.INFORMATION
                }
                
                dialogue_type = dialogue_types.get(dialogue_type_str, DialogueType.QUESTION_ANSWER)
                self.conversation_manager.start_conversation(
                    conversation_id,
                    dialogue_type=dialogue_type,
                    required_fields=required_fields
                )
            
            # Process user message
            result = self.conversation_manager.add_user_message(conversation_id, user_text)
            
            return {
                'status': 'success',
                'conversation_id': conversation_id,
                'turn_number': result.get('turn_number'),
                'user_message': result.get('user_message'),
                'assistant_response': result.get('assistant_response'),
                'progress': result.get('progress'),
                'state': result.get('state'),
                'collected_data': result.get('collected_data'),
                'pending_clarifications': result.get('pending_clarifications')
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def handle_conversation_summary(self, command_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get conversation summary and state.
        
        Args:
            command_params: Dict with 'conversation_id'
            
        Returns:
            Dict with conversation summary
        """
        if not self.conversation_manager:
            return {
                'status': 'error',
                'message': 'Conversation manager not initialized'
            }

        try:
            conversation_id = command_params.get('conversation_id')
            
            if not conversation_id:
                return {
                    'status': 'error',
                    'message': 'Conversation ID required'
                }
            
            summary = self.conversation_manager.get_conversation_summary(conversation_id)
            
            return {
                'status': 'success',
                'summary': summary
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def handle_visual_calendar_analysis(self, command_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate visual calendar analysis (heatmap, busiest day, etc).
        
        Args:
            command_params: Dict with 'calendar_events', 'analysis_type' (day|week|month)
            
        Returns:
            Dict with visual analysis and descriptions
        """
        if not self.visual_calendar:
            return {
                'status': 'error',
                'message': 'Visual calendar not initialized'
            }

        try:
            events = command_params.get('calendar_events', [])
            analysis_type = command_params.get('analysis_type', 'day')
            
            if analysis_type == 'day' and events:
                # Analyze single day
                analysis = self.visual_calendar.analyze_day(
                    events,
                    command_params.get('date', '2024-03-15')
                )
                description = self.visual_calendar.generate_visual_description(analysis)
                stress_recs = self.visual_calendar.get_stress_recommendations(
                    self.visual_calendar.analyze_month([])
                )
                
                return {
                    'status': 'success',
                    'analysis_type': 'day',
                    'description': description,
                    'stress_level': analysis.stress_level.value,
                    'utilization': f"{analysis.capacity_percentage:.0f}%",
                    'event_count': analysis.event_count,
                    'free_slots': analysis.free_slots,
                    'recommendations': stress_recs[:3]
                }
            
            return {
                'status': 'success',
                'analysis_type': analysis_type,
                'message': f'Visual analysis generated for {analysis_type}'
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def handle_accessibility_request(self, command_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle accessibility requests (audio-only mode, voice correction, etc).
        
        Args:
            command_params: Dict with 'mode' (audio_only, screen_reader, etc),
                          'voice_command' (optional), 'speech_rate' (optional)
            
        Returns:
            Dict with accessibility response
        """
        if not self.accessibility_manager:
            return {
                'status': 'error',
                'message': 'Accessibility manager not initialized'
            }

        try:
            mode = command_params.get('mode')
            voice_command = command_params.get('voice_command')
            speech_rate = command_params.get('speech_rate')
            
            # Set mode if provided
            if mode == 'audio_only':
                self.accessibility_manager.enable_audio_only_mode()
            elif mode == 'screen_reader':
                self.accessibility_manager.enable_screen_reader_mode()
            
            # Set speech rate if provided
            if speech_rate:
                rate_map = {
                    'slow': SpeechRate.SLOW,
                    'normal': SpeechRate.NORMAL,
                    'fast': SpeechRate.FAST
                }
                if speech_rate in rate_map:
                    self.accessibility_manager.set_speech_rate(rate_map[speech_rate])
            
            # Process voice command with error correction
            if voice_command:
                correction = self.accessibility_manager.process_voice_command(voice_command)
                return {
                    'status': 'success',
                    'mode': mode or 'updated',
                    'command_result': correction,
                    'is_correction': correction.get('is_correction', False),
                    'message': 'Voice command processed'
                }
            
            return {
                'status': 'success',
                'mode': mode or 'updated',
                'message': 'Accessibility settings updated'
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def handle_parse_event(self, command_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse natural language event description into structured format.
        
        Args:
            command_params: Dict with 'text' (NL event description)
            
        Returns:
            Dict with parsed event structure
        """
        try:
            text = command_params.get('text', '')
            if not text:
                return {'status': 'error', 'message': 'No text provided'}
            
            # Parse the natural language event
            parsed_event = parse_natural_language_event(text)
            
            return {
                'status': 'success',
                'event': parsed_event,
                'message': 'Event parsed successfully'
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def handle_suggest_times(self, command_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest best meeting times based on availability.
        
        Args:
            command_params: Dict with 'duration', 'participants', 'constraints'
            
        Returns:
            Dict with suggested time slots
        """
        if not self.scheduler:
            return {'status': 'error', 'message': 'Scheduler not initialized'}
        
        try:
            duration = command_params.get('duration', 60)
            participants = command_params.get('participants', [])
            constraints = command_params.get('constraints', {})
            
            # Get calendar service
            if not self.calendar_service:
                return {'status': 'error', 'message': 'Calendar service not available'}
            
            # Get free busy times
            prefs = SchedulePreferences(
                duration_minutes=duration,
                preferred_start_hour=constraints.get('start_hour', 9),
                preferred_end_hour=constraints.get('end_hour', 17)
            )
            
            suggested_times = self.scheduler.find_optimal_meeting_time(
                calendar_service=self.calendar_service,
                duration_minutes=duration,
                preferences=prefs
            )
            
            return {
                'status': 'success',
                'suggested_times': suggested_times,
                'message': f'Found {len(suggested_times)} suggested time slots'
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def handle_summarize(self, command_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize calendar events or meetings.
        
        Args:
            command_params: Dict with 'events' list or 'event_ids'
            
        Returns:
            Dict with summary information
        """
        if not self.agenda_service:
            return {'status': 'error', 'message': 'Agenda service not initialized'}
        
        try:
            events = command_params.get('events', [])
            
            if not events:
                return {'status': 'error', 'message': 'No events provided'}
            
            # Convert to AgendaEvent objects
            agenda_events = []
            for event in events:
                agenda_events.append(AgendaEvent(
                    event_id=event.get('id', ''),
                    title=event.get('summary', ''),
                    description=event.get('description', ''),
                    start=event.get('start', ''),
                    end=event.get('end', ''),
                    attendees=event.get('attendees', [])
                ))
            
            # Generate summary
            summary = self.agenda_service.generate_executive_summary(agenda_events)
            
            return {
                'status': 'success',
                'summary': summary,
                'event_count': len(events),
                'message': 'Summary generated'
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def handle_briefing(self, command_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate daily briefing with events, predictions, and recommendations.
        
        Args:
            command_params: Dict with optional 'date' or 'use_today'
            
        Returns:
            Dict with briefing information
        """
        if not self.agenda_service or not self.scheduler or not self.pattern_service:
            return {'status': 'error', 'message': 'Services not initialized'}
        
        try:
            # Get today's events from calendar
            if not self.calendar_service:
                return {'status': 'error', 'message': 'Calendar service not available'}
            
            # Get events for today
            today = datetime.now().date()
            start_time = datetime.combine(today, datetime.min.time()).isoformat() + 'Z'
            end_time = datetime.combine(today, datetime.max.time()).isoformat() + 'Z'
            
            results = self.calendar_service.events().list(
                calendarId='primary',
                timeMin=start_time,
                timeMax=end_time,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = results.get('items', [])
            
            if not events:
                return {
                    'status': 'success',
                    'briefing': 'No events scheduled for today',
                    'events': [],
                    'message': 'Daily briefing generated'
                }
            
            # Convert to AgendaEvent objects
            agenda_events = []
            for event in events:
                agenda_events.append(AgendaEvent(
                    event_id=event.get('id', ''),
                    title=event.get('summary', ''),
                    description=event.get('description', ''),
                    start=event.get('start', {}).get('dateTime', ''),
                    end=event.get('end', {}).get('dateTime', ''),
                    attendees=event.get('attendees', [])
                ))
            
            # Generate briefing summary
            summary = self.agenda_service.generate_executive_summary(agenda_events)
            
            # Get pattern predictions
            predictions = self.pattern_service.detect_patterns(events)
            
            return {
                'status': 'success',
                'briefing': summary,
                'events': [
                    {
                        'title': e.title,
                        'start': e.start,
                        'end': e.end,
                        'attendees': e.attendees
                    } for e in agenda_events
                ],
                'predictions': predictions,
                'message': 'Daily briefing generated successfully'
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _get_action_steps(self, category: str, events: List[Dict]) -> List[str]:
        """Get specific action steps for a prediction category."""
        steps = {
            'learning_blocks': [
                'Identify your most consistently busy time slots',
                'Block these slots for focused learning sessions',
                'Set them as recurring calendar blocks',
                'Add learning goals/topics to each block'
            ],
            'travel_time': [
                'Review events scheduled 5-15 minutes apart',
                'Add 15-30 minute buffer before each meeting',
                'Mark buffers as "travel time" or "transition"',
                'Enable reminders for travel buffers'
            ],
            'reminder': [
                'Find all events starting before 9am',
                'Add 10-15 minute earlier reminders',
                'Set notification type to alert/popup',
                'Test with next early morning event'
            ],
            'focus_time': [
                'Identify your least busy day/time',
                'Block 2-3 hour focus time slots',
                'Disable notifications during focus blocks',
                'Use for deep work, learning, or projects'
            ],
            'break': [
                'List all back-to-back event sequences',
                'Insert 15-30 min breaks between meetings',
                'Use for stretching, coffee, or meditation',
                'Make breaks recurring if pattern repeats'
            ]
        }
        return steps.get(category, ['Review recommendation', 'Make changes to calendar', 'Monitor results'])


# Flask endpoint integration (to be used in web_app.py)
def create_scheduler_endpoints(app, scheduler_handler):
    """
    Register Flask routes for scheduler functionality.
    
    Usage in web_app.py:
        from src.scheduler_handler import create_scheduler_endpoints
        handler = SchedulerCommandHandler()
        create_scheduler_endpoints(app, handler)
    """
    
    @app.route('/api/schedule/find-best-times', methods=['POST'])
    def find_best_times_api():
        """
        API endpoint to find best times.
        
        POST body:
        {
            "event_description": "2-hour meeting",
            "duration_minutes": 120,
            "search_window_days": 7
        }
        """
        try:
            data = request.get_json()
            results = scheduler_handler.handle_find_best_time(data)
            formatted = scheduler_handler.format_recommendations_for_dashboard(results)
            return jsonify(formatted), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/schedule/parse-and-recommend', methods=['POST'])
    def parse_and_recommend_api():
        """
        API endpoint for natural language booking.
        
        POST body:
        {
            "text": "Find the best time for a 2-hour session next week"
        }
        """
        try:
            data = request.get_json()
            user_text = data.get('text', '')
            if not user_text:
                return jsonify({'error': 'No text provided'}), 400

            results = scheduler_handler.handle_smart_booking_with_nlu(user_text)
            formatted = scheduler_handler.format_recommendations_for_dashboard(results)
            return jsonify(formatted), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/schedule/voice-response', methods=['POST'])
    def voice_response_api():
        """
        Generate voice response for recommendations.
        
        POST body:
        {
            "results": <results dict from find_best_times>
        }
        """
        try:
            data = request.get_json()
            results = data.get('results', {})
            voice_text = scheduler_handler.format_recommendations_for_voice(results)
            return jsonify({'voice_response': voice_text}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/schedule/agenda-summary', methods=['POST'])
    def agenda_summary_api():
        """
        Get calendar agenda summary.
        
        POST body:
        {
            "period": "day" | "week" | "month",
            "use_gpt": true | false,
            "calendar_events": [... Google Calendar events ...]  // optional
        }
        """
        try:
            data = request.get_json()
            period = data.get('period', 'day')
            use_gpt = data.get('use_gpt', False)
            events = data.get('calendar_events', [])
            
            result = scheduler_handler.handle_agenda_summary(
                {'period': period, 'use_gpt': use_gpt},
                calendar_events=events
            )
            
            formatted = scheduler_handler.format_summary_for_dashboard(result)
            return jsonify(formatted), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/schedule/agenda-voice', methods=['POST'])
    def agenda_voice_api():
        """
        Get voice-formatted agenda summary.
        
        POST body:
        {
            "result": <summary result from agenda-summary endpoint>
        }
        """
        try:
            data = request.get_json()
            result = data.get('result', {})
            voice_response = scheduler_handler.format_summary_for_voice(result)
            return jsonify({'voice_response': voice_response}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/schedule/predictions', methods=['POST'])
    def predictions_api():
        """
        Analyze calendar and predict user patterns/needs.
        
        POST body:
        {
            "calendar_events": [...]  # optional, fetches from Google if omitted
        }
        """
        try:
            data = request.get_json() or {}
            result = scheduler_handler.handle_predict_patterns(data)
            return jsonify(result), 200 if result.get('status') == 'success' else 400
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 400

    @app.route('/api/schedule/apply-prediction', methods=['POST'])
    def apply_prediction_api():
        """
        Apply a specific prediction/recommendation.
        
        POST body:
        {
            "prediction_id": "pred_1",
            "calendar_events": [...]
        }
        """
        try:
            data = request.get_json() or {}
            result = scheduler_handler.handle_apply_prediction(data)
            return jsonify(result), 200 if result.get('status') == 'success' else 400
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 400

    @app.route('/api/tasks/extract', methods=['POST'])
    def extract_tasks_api():
        """
        Extract tasks from conversational text.
        
        POST body:
        {
            "text": "I must renew my license before Thursday and book that dentist appointment"
        }
        """
        try:
            data = request.get_json() or {}
            result = scheduler_handler.handle_task_extraction(data)
            return jsonify(result), 200 if result.get('status') == 'success' else 400
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 400

    @app.route('/api/conversation/turn', methods=['POST'])
    def conversation_turn_api():
        """
        Process a single turn in a multi-turn conversation (Jarvis-style).
        
        POST body:
        {
            "conversation_id": "conv_123",
            "text": "User message here",
            "dialogue_type": "scheduling",  # optional: scheduling, task_creation, qa, etc.
            "required_fields": ["date", "time"]  # optional
        }
        """
        try:
            data = request.get_json() or {}
            result = scheduler_handler.handle_conversation_turn(data)
            return jsonify(result), 200 if result.get('status') == 'success' else 400
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 400

    @app.route('/api/conversation/summary', methods=['POST'])
    def conversation_summary_api():
        """
        Get conversation summary and state.
        
        POST body:
        {
            "conversation_id": "conv_123"
        }
        """
        try:
            data = request.get_json() or {}
            result = scheduler_handler.handle_conversation_summary(data)
            return jsonify(result), 200 if result.get('status') == 'success' else 400
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 400

    @app.route('/api/calendar/visual-analysis', methods=['POST'])
    def visual_calendar_api():
        """
        Generate visual calendar analysis (heatmap, stress levels, availability).
        
        POST body:
        {
            "calendar_events": [...],
            "analysis_type": "day" | "week" | "month",
            "date": "2024-03-15" (optional)
        }
        """
        try:
            data = request.get_json() or {}
            result = scheduler_handler.handle_visual_calendar_analysis(data)
            return jsonify(result), 200 if result.get('status') == 'success' else 400
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 400

    @app.route('/api/accessibility/settings', methods=['POST'])
    def accessibility_settings_api():
        """
        Configure accessibility settings (audio-only mode, speech rate, etc).
        
        POST body:
        {
            "mode": "audio_only" | "screen_reader" | "high_contrast",
            "speech_rate": "slow" | "normal" | "fast",
            "voice_command": "optional voice command text"
        }
        """
        try:
            data = request.get_json() or {}
            result = scheduler_handler.handle_accessibility_request(data)
            return jsonify(result), 200 if result.get('status') == 'success' else 400
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 400

    @app.route('/api/parse_event', methods=['POST'])
    def parse_event_api():
        """
        Parse natural language event description into structured format.
        
        POST body:
        {
            "text": "Meeting with John tomorrow at 2pm to discuss Q1 strategy"
        }
        """
        try:
            data = request.get_json() or {}
            result = scheduler_handler.handle_parse_event(data)
            return jsonify(result), 200 if result.get('status') == 'success' else 400
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 400

    @app.route('/api/suggest_times', methods=['POST'])
    def suggest_times_api():
        """
        Suggest best meeting times based on availability.
        
        POST body:
        {
            "duration": 60,
            "participants": ["john@example.com", "jane@example.com"],
            "constraints": {"start_hour": 9, "end_hour": 17}
        }
        """
        try:
            data = request.get_json() or {}
            result = scheduler_handler.handle_suggest_times(data)
            return jsonify(result), 200 if result.get('status') == 'success' else 400
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 400

    @app.route('/api/summarize', methods=['POST'])
    def summarize_api():
        """
        Summarize calendar events or meetings.
        
        POST body:
        {
            "events": [
                {"id": "123", "summary": "Meeting", "description": "...", "start": "...", "end": "...", "attendees": []}
            ]
        }
        """
        try:
            data = request.get_json() or {}
            result = scheduler_handler.handle_summarize(data)
            return jsonify(result), 200 if result.get('status') == 'success' else 400
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 400

    @app.route('/api/briefing', methods=['POST'])
    def briefing_api():
        """
        Generate daily briefing with events, predictions, and recommendations.
        
        POST body:
        {
            "use_today": true
        }
        """
        try:
            data = request.get_json() or {}
            result = scheduler_handler.handle_briefing(data)
            return jsonify(result), 200 if result.get('status') == 'success' else 400
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 400