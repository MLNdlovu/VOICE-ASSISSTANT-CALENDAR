"""
Calendar Blueprint for Voice Assistant Calendar
Handles calendar operations, booking, events, and calendar-related API endpoints
"""

import os
import json
import logging
from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, request, jsonify, session, send_from_directory, abort, redirect, url_for
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Import existing modules
import sys
sys.path.insert(0, './src')
import book
import get_details
from src.scheduler_handler import SchedulerCommandHandler, create_scheduler_endpoints
from src.actions.calendar_actions import create_event, get_events, cancel_event

# Import conflict detection
try:
    from src.calendar_conflict import ConflictDetector, TimeSlot
except ImportError:
    ConflictDetector = None
    TimeSlot = None

calendar_bp = Blueprint('calendar', __name__)

def login_required(f):
    """Decorator to require login."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_calendar_service(access_token=None):
    """Build and return a Google Calendar service with current credentials."""
    if not access_token and 'access_token' not in session:
        return None

    token = access_token or session.get('access_token')
    if not token:
        return None

    try:
        creds = Credentials(token=token)
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error building service: {e}")
        return None

@calendar_bp.route('/unified')
@login_required
def unified_dashboard():
    """Voice demo dashboard - simplified interface for demo."""
    # Ensure voice state is initialized
    if 'voice_state' not in session:
        session['voice_state'] = 'active'
    if 'booking_context' not in session:
        session['booking_context'] = {}
    
    user_name = session.get('user_firstname', 'Welcome')
    return render_template('voice_demo.html', user_name=user_name)

@calendar_bp.route('/ai')
@login_required
def ai_chat():
    """Dedicated AI chat page with premium voice interface."""
    user_email = session.get('user_email', 'User')
    user_name = session.get('user_firstname', 'Welcome')
    user_trigger = session.get('user_trigger', 'XX00')

    return render_template('ai_chat.html',
                         user_name=user_name,
                         user_email=user_email,
                         user_trigger=user_trigger)

@calendar_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page."""
    return render_template('dashboard.html', user_email=session.get('user_email'))

@calendar_bp.route('/docs/<path:filename>')
@login_required
def serve_docs(filename):
    """Serve markdown docs from the local docs/ folder."""
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs')
    path = os.path.join(docs_dir, filename)
    if not os.path.exists(path):
        abort(404)

    # If python-markdown is installed, render markdown to HTML for nicer display
    try:
        import markdown
        with open(path, 'r', encoding='utf-8') as f:
            md = f.read()
        html = markdown.markdown(md, extensions=['fenced_code', 'tables'])
        # Simple wrapper page
        return f"<html><head><meta charset='utf-8'><title>{filename}</title><style>body{{background:#07132a;color:#eaf6ff;font-family:Segoe UI, Tahoma, Geneva, Verdana,sans-serif;padding:24px}} a{{color:#4fb0ff}}</style></head><body>{html}</body>"
    except Exception:
        return send_from_directory(docs_dir, filename)

# --- API Endpoints ---

@calendar_bp.route('/api/events', methods=['GET'])
@login_required
def get_events_api():
    """Get upcoming events."""
    try:
        service = get_calendar_service()
        if not service:
            return jsonify({'error': 'Not authenticated'}), 401

        now = datetime.now(timezone.utc).isoformat()
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        # Format events
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            formatted_events.append({
                'id': event['id'],
                'summary': event.get('summary', 'Untitled'),
                'start': start,
                'end': end,
                'description': event.get('description', ''),
                'organizer': event.get('organizer', {}).get('email', '')
            })

        return jsonify(formatted_events)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@calendar_bp.route('/api/events/<event_id>/description', methods=['PATCH'])
@login_required
def update_event_description(event_id):
    """Update the description of an existing event."""
    try:
        data = request.get_json() or {}
        new_description = data.get('description', '')
        # mode: 'overwrite' (default) or 'append'
        mode = data.get('mode', 'overwrite')
        if new_description is None:
            return jsonify({'error': 'No description provided'}), 400

        if mode not in ('overwrite', 'append'):
            return jsonify({'error': 'Invalid mode. Use "overwrite" or "append".'}), 400

        service = get_calendar_service()
        if not service:
            return jsonify({'error': 'Not authenticated'}), 401

        # Fetch existing event to preserve other fields
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        existing = event.get('description', '') or ''

        if mode == 'append' and existing:
            # Append with a clear separator and newline
            sep = '\n\n---\n\n'
            event['description'] = existing + sep + new_description
        else:
            # Overwrite or append when no existing description
            event['description'] = new_description

        updated = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()

        return jsonify({'success': True, 'event': updated})
    except HttpError as he:
        return jsonify({'error': str(he)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@calendar_bp.route('/api/book', methods=['POST'])
@login_required
def book_event():
    """Book a new event."""
    try:
        data = request.get_json()

        email = data.get('email') or session.get('user_email')
        date = data.get('date')
        time = data.get('time')
        summary = data.get('summary', 'Event')
        duration = data.get('duration', 30)

        if not all([email, date, time]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Parse date/time
        try:
            from dateutil import parser as date_parser
            parsed_date = date_parser.parse(date).strftime('%Y-%m-%d')
        except Exception:
            parsed_date = date

        start_iso = f"{parsed_date}T{time}:00+02:00"

        service = get_calendar_service()
        if not service:
            return jsonify({'error': 'Not authenticated'}), 401

        # Conflict detection: check for overlapping events before creating
        try:
            if ConflictDetector and TimeSlot:
                import datetime as _dt

                proposed_start = _dt.datetime.fromisoformat(start_iso)
                proposed_end = proposed_start + _dt.timedelta(minutes=duration)
                proposed_slot = TimeSlot(proposed_start, proposed_end)

                # Query surrounding events to check for overlaps
                time_min = (proposed_start - _dt.timedelta(days=1)).isoformat()
                time_max = (proposed_end + _dt.timedelta(days=1)).isoformat()
                try:
                    events_result = service.events().list(
                        calendarId='primary',
                        timeMin=time_min,
                        timeMax=time_max,
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                    existing_events = events_result.get('items', [])
                except Exception:
                    existing_events = []

                detector = ConflictDetector()
                conflicts = detector.detect_conflicts(proposed_slot, existing_events)
                if conflicts:
                    suggestions = detector.suggest_alternatives(proposed_slot, existing_events, duration_minutes=duration, max_suggestions=3)
                    return jsonify({'error': 'Conflicting events', 'conflicts': conflicts, 'suggestions': suggestions}), 409
        except Exception as e:
            # If conflict detection fails for any reason, continue to attempt create
            print(f"[WARN] Conflict detection failed: {e}")

        created = book.create_event_user(
            service,
            calendar_id='primary',
            email=email,
            start_time_iso=start_iso,
            summary=summary,
            duration_minutes=duration,
            reminders=[10]
        )

        if created:
            # Provide spoken feedback for accessibility when used via the web UI
            speak_text = f'Event booked successfully: {summary} on {parsed_date} at {time}'
            return jsonify({'success': True, 'event_id': created, 'message': f'✅ Event booked: {summary} on {parsed_date} at {time}', 'speak': True, 'speak_text': speak_text})
        else:
            return jsonify({'error': 'Failed to create event'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@calendar_bp.route('/api/set-reminder', methods=['POST'])
@login_required
def set_reminder():
    """Set a reminder for a specific time."""
    try:
        data = request.get_json()

        email = data.get('email') or session.get('user_email')
        date = data.get('date')
        time = data.get('time')
        summary = data.get('summary', 'Reminder')
        reminder_minutes = data.get('reminder_minutes', 0)

        if not all([email, date, time]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Parse date/time
        try:
            from dateutil import parser as date_parser
            parsed_date = date_parser.parse(date).strftime('%Y-%m-%d')
        except Exception:
            parsed_date = date

        start_iso = f"{parsed_date}T{time}:00+02:00"

        service = get_calendar_service()
        if not service:
            return jsonify({'error': 'Not authenticated'}), 401

        # Create reminder as a calendar event
        created = book.create_event_user(
            service,
            calendar_id='primary',
            email=email,
            start_time_iso=start_iso,
            summary=f"🔔 {summary}",
            duration_minutes=5,  # Short duration for reminders
            reminders=[reminder_minutes] if reminder_minutes > 0 else [5]
        )

        if created:
            speak_text = f'Reminder set for {summary} on {parsed_date} at {time}'
            return jsonify({
                'success': True,
                'event_id': created,
                'message': f'🔔 Reminder set: {summary} on {parsed_date} at {time}',
                'speak': True,
                'speak_text': speak_text
            })
        else:
            return jsonify({'error': 'Failed to create reminder'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@calendar_bp.route('/api/cancel/<event_id>', methods=['DELETE'])
@login_required
def cancel_event_api(event_id):
    """Cancel an event."""
    try:
        service = get_calendar_service()
        if not service:
            return jsonify({'error': 'Not authenticated'}), 401

        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@calendar_bp.route('/api/settings', methods=['GET'])
@login_required
def get_settings():
    """Get user settings."""
    try:
        settings_file = os.path.join('.config', 'gui_settings.json')
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
        else:
            settings = {
                'timezone': 'Africa/Johannesburg',
                'default_event_duration': 30,
                'last_calendar_id': 'primary'
            }

        return jsonify(settings)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@calendar_bp.route('/api/settings', methods=['POST'])
@login_required
def update_settings():
    """Update user settings."""
    try:
        data = request.get_json()
        settings_file = os.path.join('.config', 'gui_settings.json')

        os.makedirs(os.path.dirname(settings_file), exist_ok=True)
        with open(settings_file, 'w') as f:
            json.dump(data, f, indent=2)

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@calendar_bp.route('/api/voice', methods=['POST'])
@login_required
def voice_command():
    """
    Process voice commands from the web UI.
    Accepts voice text, parses it, and executes the command.
    """
    try:
        data = request.get_json()
        voice_text = data.get('text', '').strip()

        if not voice_text:
            return jsonify({'error': 'No voice text provided'}), 400

        # Import voice handler to parse commands
        from voice_handler import VoiceCommandParser

        # Parse the voice command
        command, params = VoiceCommandParser.parse_command(voice_text)

        # Process the command
        if command == 'events-for-day':
            # List all events for a specific day (default today)
            date = params.get('date')
            if not date:
                from datetime import datetime
                date = datetime.now().strftime('%Y-%m-%d')
            service = get_calendar_service()
            if not service:
                return jsonify({'error': 'Not authenticated'}), 401
            from datetime import datetime, timedelta
            # Get start and end of the day in ISO format
            start_dt = datetime.strptime(date, '%Y-%m-%d')
            end_dt = start_dt + timedelta(days=1)
            start_iso = start_dt.isoformat() + 'T00:00:00+00:00' if 'T' not in date else date
            end_iso = end_dt.isoformat() + 'T00:00:00+00:00'
            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_iso,
                timeMax=end_iso,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            if events:
                event_list = ', '.join([e.get('summary', 'Untitled') + ' at ' + e['start'].get('dateTime', e['start'].get('date', ''))[11:16] for e in events])
                speak_text = f'You have {len(events)} events for {date}. ' + event_list
                message = f'Events for {date}: ' + event_list
            else:
                speak_text = f'You have no events for {date}.'
                message = f'No events for {date}.'
            return jsonify({
                'success': True,
                'command': command,
                'events': events,
                'message': message,
                'speak': True,
                'speak_text': speak_text
            })
        elif command == 'book':
            # Book an event
            email = params.get('email') or session.get('user_email')
            date = params.get('date')
            time = params.get('time')
            summary = params.get('summary', 'Event')

            if not all([email, date, time]):
                return jsonify({'error': 'Missing date or time in voice command. Please provide all details.', 'command': command, 'params': params}), 400

            service = get_calendar_service()
            if not service:
                return jsonify({'error': 'Not authenticated'}), 401

            start_iso = f"{date}T{time}:00+02:00"
            created = book.create_event_user(
                service,
                calendar_id='primary',
                email=email,
                start_time_iso=start_iso,
                summary=summary,
                duration_minutes=30,
                reminders=[10]
            )

            if created:
                speak_text = f'Meeting booked successfully. {summary} on {date} at {time}'
                return jsonify({
                    'success': True,
                    'command': command,
                    'message': f'✅ Event booked: {summary} on {date} at {time}',
                    'event_id': created,
                    'speak': True,
                    'speak_text': speak_text
                })
            else:
                speak_text = 'Failed to create event. Please try again.'
                return jsonify({'error': 'Failed to create event', 'command': command, 'speak': True, 'speak_text': speak_text}), 500

        elif command == 'cancel-book':
            # Cancel an event
            date = params.get('date')
            time = params.get('time')

            if not all([date, time]):
                return jsonify({'error': 'Please specify date and time to cancel', 'command': command}), 400

            service = get_calendar_service()
            if not service:
                return jsonify({'error': 'Not authenticated'}), 401

            start_iso = f"{date}T{time}:00+02:00"
            cancelled = book.cancel_event_by_start(service, calendar_id='primary', start_time_iso=start_iso)

            if cancelled:
                speak_text = f'Event cancelled successfully on {date} at {time}'
                return jsonify({
                    'success': True,
                    'command': command,
                    'message': f'✅ Event cancelled on {date} at {time}',
                    'speak': True,
                    'speak_text': speak_text
                })
            else:
                speak_text = 'Event not found. Please check the date and time.'
                return jsonify({'error': 'Event not found', 'command': command, 'speak': True, 'speak_text': speak_text}), 404

        elif command == 'events':
            # Show events for specific day (if date provided) or today
            service = get_calendar_service()
            if not service:
                return jsonify({'error': 'Not authenticated'}), 401

            # Get the date to query (default to today)
            date_str = params.get('date')
            if not date_str:
                date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')

            try:
                # Parse the target date and get start/end of that day
                target_date = datetime.strptime(date_str, '%Y-%m-%d')
                start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

                # Convert to ISO format with timezone
                start_iso = start_of_day.isoformat() + 'Z'
                end_iso = end_of_day.isoformat() + 'Z'

                events_result = service.events().list(
                    calendarId='primary',
                    timeMin=start_iso,
                    timeMax=end_iso,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()

                events = events_result.get('items', [])
                event_count = len(events)

                # Format event list
                event_summaries = []
                for e in events:
                    title = e.get('summary', 'Untitled')
                    start = e.get('start', {}).get('dateTime') or e.get('start', {}).get('date')
                    if start and 'T' in str(start):
                        time_part = str(start).split('T')[1][:5]  # HH:MM
                        event_summaries.append(f"{title} at {time_part}")
                    else:
                        event_summaries.append(title)

                if event_summaries:
                    event_text = ', '.join(event_summaries[:5])  # Limit to 5 for speech
                    speak_text = f'You have {event_count} events on {date_str}: {event_text}'
                else:
                    speak_text = f'You have no events on {date_str}'

                return jsonify({
                    'success': True,
                    'command': command,
                    'events': events,
                    'message': f'Events for {date_str}: {event_count} found',
                    'speak': True,
                    'speak_text': speak_text
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        elif command == 'help':
            # Show available commands
            speak_text = 'Available commands are: book a meeting, cancel a booking, view events, help, share calendar, and config. Say any of these commands to get started.'
            return jsonify({
                'success': True,
                'command': command,
                'message': 'Available commands: book, cancel-book, events, help, share, config, exit',
                'speak': True,
                'speak_text': speak_text
            })

        elif command == 'share':
            # Calendar sharing instructions
            speak_text = 'To share your calendar, go to Google Calendar settings, select your calendar, and add collaborator emails.'
            return jsonify({
                'success': True,
                'command': command,
                'message': 'Share your calendar by opening Google Calendar settings and adding collaborators.',
                'speak': True,
                'speak_text': speak_text
            })

        else:
            # Unknown command
            speak_text = f'Unknown command. Please try saying: book a meeting, cancel a booking, view events, get help, or share calendar'
            return jsonify({
                'success': False,
                'command': command,
                'message': f'Unknown command: {voice_text}. Try "book", "cancel", "events", or "help"',
                'speak': True,
                'speak_text': speak_text
            }), 400

    except Exception as e:
        speak_text = 'An error occurred. Please try again.'
        return jsonify({'error': str(e), 'type': 'exception', 'speak': True, 'speak_text': speak_text}), 500
