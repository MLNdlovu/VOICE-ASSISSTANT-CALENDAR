import os
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

voice_bp = Blueprint('voice', __name__)

# Voice session storage (in production, use database)
voice_sessions = {}

# Voice command logging setup
voice_logger = logging.getLogger('voice_assistant')


def get_calendar_service():
    """Build and return a Google Calendar service with current credentials."""
    if 'access_token' not in session:
        return None
    
    token = session.get('access_token')
    if not token:
        return None
    
    try:
        creds = Credentials(token=token)
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"[ERROR] Error building calendar service: {e}")
        return None


@voice_bp.route('/api/voice/start', methods=['POST'])
def start_voice_session():
    """Start a new voice assistant session"""
    try:
        # Check if user is authenticated
        if 'user_email' not in session:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401

        # Create new session
        session_id = str(uuid.uuid4())
        user_trigger = session.get('user_trigger', 'XX00')
        user_name = session.get('user_firstname', 'User')
        
        # Initialize voice state in session
        session['voice_state'] = 'active'
        session['booking_context'] = {}

        voice_sessions[session_id] = {
            'session_id': session_id,
            'user_email': session['user_email'],
            'user_trigger': user_trigger,
            'user_name': user_name,
            'voice_state': 'active',
            'start_time': datetime.now(timezone.utc),
            'transcript': [],
            'turn_count': 0,
            'booking_context': {}
        }

        # Log session start
        voice_logger.info(f"Voice session started: {session_id} for {user_name}")

        return jsonify({
            'success': True,
            'session_id': session_id,
            'user_trigger': user_trigger,  # Internal only, not displayed
            'user_name': user_name,
            'voice_state': 'active',
            'greeting': f"I'm ready. How can I help you?",
            'speak_text': "I'm ready. How can I help you?"
        })

    except Exception as e:
        voice_logger.error(f"Error starting voice session: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to start voice session'
        }), 500


@voice_bp.route('/api/voice/process-command', methods=['POST'])
def process_voice_command():
    """Process a simple voice command with state machine"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip().lower()
        
        if not text:
            return jsonify({
                'success': False,
                'error': 'No text provided'
            }), 400

        user_name = session.get('user_firstname', 'User')
        booking_context = session.get('booking_context', {})
        voice_state = session.get('voice_state', 'active')

        # Check if we're in booking flow
        if voice_state == 'booking_name':
            # User is providing event name
            booking_context['name'] = text
            session['booking_context'] = booking_context
            session['voice_state'] = 'booking_date'
            return jsonify({
                'success': True,
                'state': 'booking_date',
                'speak_text': "What day should I schedule this for?",
                'message': "What day? (e.g., today, tomorrow, monday)"
            })
        
        elif voice_state == 'booking_date':
            # User is providing date
            # Simple date parsing
            booking_context['date'] = text
            session['booking_context'] = booking_context
            session['voice_state'] = 'booking_time'
            return jsonify({
                'success': True,
                'state': 'booking_time',
                'speak_text': "What time should it start?",
                'message': "What time? (e.g., 10am, 2:30pm)"
            })
        
        elif voice_state == 'booking_time':
            # User is providing time - create event
            booking_context['time'] = text
            session['booking_context'] = booking_context
            session['voice_state'] = 'active'
            
            # Attempt to create event
            service = get_calendar_service()
            if not service:
                return jsonify({
                    'success': False,
                    'speak_text': "I couldn't connect to your calendar. Please try again.",
                    'message': "Calendar service unavailable"
                })
            
            # Parse date and time
            event_name = booking_context.get('name', 'Meeting')
            event_date = booking_context.get('date', '')
            event_time = booking_context.get('time', '10:00')
            
            # Simple ISO date/time construction (for demo)
            try:
                # Build ISO datetime (simplified)
                now = datetime.now(timezone.utc)
                if 'today' in event_date:
                    event_dt = now
                elif 'tomorrow' in event_date:
                    event_dt = now + timedelta(days=1)
                else:
                    # Default to tomorrow
                    event_dt = now + timedelta(days=1)
                
                # Parse time (simple format like "10am" or "2:30pm")
                import re
                time_match = re.search(r'(\d{1,2}):?(\d{0,2})\s*(am|pm)?', event_time)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2)) if time_match.group(2) else 0
                    if time_match.group(3) == 'pm' and hour < 12:
                        hour += 12
                    elif time_match.group(3) == 'am' and hour == 12:
                        hour = 0
                    event_dt = event_dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    event_dt = event_dt.replace(hour=10, minute=0, second=0, microsecond=0)
                
                # Create event
                event = {
                    'summary': event_name,
                    'start': {
                        'dateTime': event_dt.isoformat(),
                        'timeZone': 'UTC'
                    },
                    'end': {
                        'dateTime': (event_dt + timedelta(minutes=30)).isoformat(),
                        'timeZone': 'UTC'
                    }
                }
                
                created_event = service.events().insert(calendarId='primary', body=event).execute()
                
                return jsonify({
                    'success': True,
                    'speak_text': f"Event '{event_name}' booked successfully.",
                    'message': f"✅ Event booked: {event_name}",
                    'event_id': created_event.get('id')
                })
            
            except Exception as e:
                voice_logger.error(f"Error creating event: {e}")
                return jsonify({
                    'success': False,
                    'speak_text': "Failed to create the event. Please try again.",
                    'message': f"Error: {str(e)}"
                })

        # ACTIVE STATE - Parse main commands
        if voice_state == 'active':
            # Check for "book" or "add"
            if any(word in text for word in ['book', 'add', 'schedule', 'create']):
                session['voice_state'] = 'booking_name'
                session['booking_context'] = {'step': 'name'}
                return jsonify({
                    'success': True,
                    'state': 'booking_name',
                    'speak_text': "What should I name the event?",
                    'message': "What should I name the event?"
                })
            
            # Check for "show" or "list events"
            elif any(word in text for word in ['show', 'list', 'events', 'calendar', 'today', 'tomorrow', 'week']):
                service = get_calendar_service()
                if not service:
                    return jsonify({
                        'success': False,
                        'speak_text': "I couldn't connect to your calendar.",
                        'message': "Calendar service unavailable"
                    })
                
                # Determine which day(s) to fetch
                if 'tomorrow' in text:
                    target_date = datetime.now(timezone.utc) + timedelta(days=1)
                    day_label = 'tomorrow'
                elif 'week' in text:
                    target_date = datetime.now(timezone.utc)
                    day_label = 'this week'
                else:
                    target_date = datetime.now(timezone.utc)
                    day_label = 'today'
                
                try:
                    # Get events for the day
                    if 'week' in text:
                        # Week view: next 7 days
                        start_dt = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                        end_dt = start_dt + timedelta(days=7)
                    else:
                        # Day view
                        start_dt = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                        end_dt = start_dt + timedelta(days=1)
                    
                    events_result = service.events().list(
                        calendarId='primary',
                        timeMin=start_dt.isoformat(),
                        timeMax=end_dt.isoformat(),
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                    
                    events = events_result.get('items', [])
                    
                    if events:
                        event_list = []
                        for e in events:
                            title = e.get('summary', 'Untitled')
                            start = e.get('start', {}).get('dateTime', e.get('start', {}).get('date', ''))
                            if start and 'T' in str(start):
                                time_str = start.split('T')[1][:5]
                                event_list.append(f"{title} at {time_str}")
                            else:
                                event_list.append(title)
                        
                        event_text = ', '.join(event_list)
                        speak_text = f"You have {len(events)} events {day_label}: {event_text}"
                    else:
                        speak_text = f"You have no events {day_label}."
                    
                    return jsonify({
                        'success': True,
                        'state': 'active',
                        'speak_text': speak_text,
                        'message': speak_text,
                        'events': events
                    })
                
                except Exception as e:
                    voice_logger.error(f"Error fetching events: {e}")
                    return jsonify({
                        'success': False,
                        'speak_text': "I couldn't fetch your events.",
                        'message': f"Error: {str(e)}"
                    })
            
            # Check for "cancel"
            elif any(word in text for word in ['cancel', 'delete', 'remove']):
                service = get_calendar_service()
                if not service:
                    return jsonify({
                        'success': False,
                        'speak_text': "I couldn't connect to your calendar.",
                        'message': "Calendar service unavailable"
                    })
                
                # For demo: just ask which event
                return jsonify({
                    'success': True,
                    'state': 'asking_cancel',
                    'speak_text': "Which event would you like to cancel? Tell me the event name.",
                    'message': "Which event? (say the name or time)"
                })
            
            else:
                # Unknown command
                return jsonify({
                    'success': True,
                    'state': 'active',
                    'speak_text': "I didn't catch that. You can say: book an event, show my events, or cancel an event.",
                    'message': "Try: 'book', 'show events', or 'cancel'"
                })

        return jsonify({
            'success': False,
            'error': 'Unknown voice state'
        }), 400

    except Exception as e:
        voice_logger.error(f"Error processing voice command: {e}")
        print(f"[ERROR] Voice command error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to process command'
        }), 500


@voice_bp.route('/api/voice/end-session', methods=['POST'])
def end_voice_session():
    """End a voice session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        notes = data.get('notes', '')

        if session_id and session_id in voice_sessions:
            session_data = voice_sessions[session_id]
            duration = datetime.now(timezone.utc) - session_data['start_time']

            voice_logger.info(f"Voice session ended: {session_id} - Duration: {duration}")

            # Clean up session
            del voice_sessions[session_id]

        return jsonify({
            'success': True,
            'message': 'Session ended successfully'
        })

    except Exception as e:
        voice_logger.error(f"Error ending voice session: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to end session'
        }), 500


@voice_bp.route('/voice-interface')
def voice_interface():
    """Render the voice interface page"""
    if 'user_email' not in session:
        return redirect(url_for('login'))

    return render_template('voice_interface.html')
