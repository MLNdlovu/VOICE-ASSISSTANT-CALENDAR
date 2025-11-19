"""
Web Dashboard for Voice Assistant Calendar
Modern Flask web app with Google Calendar integration, OAuth, and responsive UI.
"""

import os
import json
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory, abort
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# IMPORTANT: Allow insecure transport (http) for local development
# In production, ALWAYS use HTTPS
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Import existing modules
import sys
sys.path.insert(0, './src')
import book
import get_details
import voice_handler
# Defer importing the optional AI module to runtime to avoid blocking imports (e.g., when openai is not installed)
initialize_chatbot = None
is_chatgpt_available = lambda: False

# Flask app setup
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(16))

# Google OAuth configuration
SCOPES = [
    # Use the canonical userinfo scopes to match what Google's token endpoint returns
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/calendar'
]

# Load client secret from .config
CLIENT_SECRET_FILE = None
for f in os.listdir('.config'):
    if f.startswith('client_secret') and f.endswith('.json'):
        CLIENT_SECRET_FILE = os.path.join('.config', f)
        break

if not CLIENT_SECRET_FILE:
    print("⚠️  Warning: client_secret JSON not found in .config/")


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


def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    """Home page - redirect to dashboard if logged in, else login page."""
    if 'access_token' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/login')
def login():
    """Show login page with OAuth button."""
    if 'access_token' in session:
        return redirect(url_for('dashboard'))
    
    # If user clicked OAuth button, this handles it
    if request.args.get('code'):
        return oauth_callback()
    
    # Default: show login page (user clicks Google OAuth button there)
    if not CLIENT_SECRET_FILE:
        return render_template('login.html', error="Client secret not configured")
    
    # User clicked the OAuth button - initiate OAuth flow
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('oauth_callback', _external=True)
    )
    
    auth_url, state = flow.authorization_url(prompt='select_account')
    session['oauth_state'] = state
    
    return redirect(auth_url)


@app.route('/oauth/callback')
def oauth_callback():
    """Handle OAuth callback."""
    if not CLIENT_SECRET_FILE:
        return "Error: Client secret not configured", 500
    
    state = session.get('oauth_state')
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=url_for('oauth_callback', _external=True)
    )
    
    try:
        flow.fetch_token(authorization_response=request.url)
        creds = flow.credentials
        
        # Store token in session
        session['access_token'] = creds.token
        session['refresh_token'] = creds.refresh_token
        session['token_expiry'] = creds.expiry.isoformat() if creds.expiry else None
        
        # Get user info
        service = build('oauth2', 'v2', credentials=creds)
        user_info = service.userinfo().get().execute()
        session['user_email'] = user_info.get('email')
        
        return redirect(url_for('dashboard'))
    
    except Exception as e:
        print(f"OAuth error: {e}")
        return f"Authentication failed: {str(e)}", 400


@app.route('/logout')
def logout():
    """Log out user."""
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page."""
    return render_template('dashboard.html', user_email=session.get('user_email'))


@app.route('/docs/<path:filename>')
@login_required
def serve_docs(filename):
    """Serve markdown docs from the local docs/ folder."""
    docs_dir = os.path.join(os.path.dirname(__file__), 'docs')
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
        return f"<html><head><meta charset='utf-8'><title>{filename}</title><style>body{{background:#07132a;color:#eaf6ff;font-family:Segoe UI, Tahoma, Geneva, Verdana,sans-serif;padding:24px}} a{{color:#4fb0ff}}</style></head><body>{html}</body></html>"
    except Exception:
        return send_from_directory(docs_dir, filename)


@app.route('/ai')
@login_required
def ai_shortlink():
    """Redirect helper so /ai opens the dashboard and triggers the modal via hash."""
    return redirect(url_for('dashboard') + '#ai')


# --- API Endpoints ---

@app.route('/api/events', methods=['GET'])
@login_required
def get_events():
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


@app.route('/api/events/<event_id>/description', methods=['PATCH'])
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


@app.route('/api/book', methods=['POST'])
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


@app.route('/api/cancel/<event_id>', methods=['DELETE'])
@login_required
def cancel_event(event_id):
    """Cancel an event."""
    try:
        service = get_calendar_service()
        if not service:
            return jsonify({'error': 'Not authenticated'}), 401
        
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings', methods=['GET'])
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


@app.route('/api/settings', methods=['POST'])
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


@app.route('/api/user', methods=['GET'])
@login_required
def get_user():
    """Get current user info."""
    return jsonify({
        'email': session.get('user_email'),
        'authenticated': True
    })


@app.route('/api/voice', methods=['POST'])
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
            # Show upcoming events
            service = get_calendar_service()
            if not service:
                return jsonify({'error': 'Not authenticated'}), 401
            
            now = datetime.now(timezone.utc).isoformat()
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=5,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            event_count = len(events)
            speak_text = f'You have {event_count} upcoming events. '
            if events:
                speak_text += f'First event: {events[0].get("summary", "Untitled")}'
            else:
                speak_text += 'No events scheduled'
            
            return jsonify({
                'success': True,
                'command': command,
                'events': events,
                'message': f'You have {len(events)} upcoming events',
                'speak': True,
                'speak_text': speak_text
            })
        
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


# --- AI Endpoints ---
_chatbot = None

def get_chatbot():
    global _chatbot
    if _chatbot is not None:
        return _chatbot
    # Try to import and initialize the chatbot on demand. Keep this lazy to avoid
    # importing heavy optional dependencies (like `openai`) during test collection.
    global initialize_chatbot, is_chatgpt_available
    if initialize_chatbot is None:
        try:
            from ai_chatgpt import initialize_chatbot as _init_cb, is_chatgpt_available as _is_avail
            initialize_chatbot = _init_cb
            is_chatgpt_available = _is_avail
        except Exception:
            initialize_chatbot = None
            is_chatgpt_available = lambda: False
            return None

    try:
        _chatbot = initialize_chatbot()
        return _chatbot
    except Exception:
        return None


@app.route('/api/ai/chat', methods=['POST'])
@login_required
def ai_chat():
    """Simple chat/assistant endpoint that forwards user messages to the AI."""
    data = request.get_json() or {}
    message = data.get('message')
    context = data.get('context')
    if not message:
        return jsonify({'error': 'No message provided'}), 400

    bot = get_chatbot()
    if not bot:
        return jsonify({'error': 'AI not configured or not available'}), 503

    try:
        ai_response = bot.chat(message, calendar_context=context)
        return jsonify({'success': True, 'response': ai_response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai/agenda', methods=['POST'])
@login_required
def ai_agenda():
    """Generate an agenda for a meeting/event using the AI."""
    data = request.get_json() or {}
    title = data.get('title', 'Meeting')
    duration = data.get('duration', 60)
    participants = data.get('participants', [])
    notes = data.get('notes', '')

    bot = get_chatbot()
    if not bot:
        return jsonify({'error': 'AI not configured or not available'}), 503

    prompt = f"Create a structured agenda for a {duration}-minute meeting titled '{title}'. Include sections, time allocations, and brief bullet points. Participants: {', '.join(participants)}. Additional notes: {notes}"
    try:
        ai_response = bot.chat(prompt)
        return jsonify({'success': True, 'agenda': ai_response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai/actions', methods=['POST'])
@login_required
def ai_actions():
    """Extract action items from meeting notes or event description."""
    data = request.get_json() or {}
    notes = data.get('notes', '')
    title = data.get('title', 'Meeting')
    if not notes:
        return jsonify({'error': 'No notes provided'}), 400

    bot = get_chatbot()
    if not bot:
        return jsonify({'error': 'AI not configured or not available'}), 503

    prompt = f"Extract concise action items from the following meeting notes for '{title}':\n\n{notes}\n\nReturn a numbered list of action items with responsible parties if mentioned." 
    try:
        ai_response = bot.chat(prompt)
        return jsonify({'success': True, 'actions': ai_response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai/email', methods=['POST'])
@login_required
def ai_email():
    """Draft an email for an event (invites, follow-ups, summary).
    Expects: title, recipients (list), body/context (notes or agenda)
    """
    data = request.get_json() or {}
    title = data.get('title', 'Meeting')
    recipients = data.get('recipients', [])
    context = data.get('context', '')

    bot = get_chatbot()
    if not bot:
        return jsonify({'error': 'AI not configured or not available'}), 503

    prompt = f"Draft a professional email about '{title}'. Recipients: {', '.join(recipients)}. Context: {context}. Include a clear subject line, brief summary, action items, and a polite closing." 
    try:
        ai_response = bot.chat(prompt)
        return jsonify({'success': True, 'email': ai_response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai/suggest-times', methods=['POST'])
@login_required
def ai_suggest_times():
    """Suggest meeting times based on participants and duration.
    Expects: duration (minutes), participants (list), preferred_days (optional)
    """
    data = request.get_json() or {}
    duration = data.get('duration', 30)
    participants = data.get('participants', [])
    preferred = data.get('preferred_days', '')

    bot = get_chatbot()
    if not bot:
        return jsonify({'error': 'AI not configured or not available'}), 503

    prompt = f"Suggest 3 available meeting time slots for a {duration}-minute meeting with participants: {', '.join(participants)}. Preferred days/times: {preferred}. Return ISO local date/time suggestions with brief justification." 
    try:
        ai_response = bot.chat(prompt)
        return jsonify({'success': True, 'suggestions': ai_response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai/summarize', methods=['POST'])
@login_required
def ai_summarize():
    """Summarize meeting notes or text using the AI."""
    data = request.get_json() or {}
    notes = data.get('notes', '')
    if not notes:
        return jsonify({'error': 'No notes provided'}), 400

    bot = get_chatbot()
    if not bot:
        return jsonify({'error': 'AI not configured or not available'}), 503

    prompt = f"Please provide a concise meeting summary and action items from the following notes:\n\n{notes}\n\nReturn a short summary and a list of action items." 
    try:
        ai_response = bot.chat(prompt)
        return jsonify({'success': True, 'summary': ai_response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai/followups', methods=['POST'])
@login_required
def ai_followups():
    """Generate suggested follow-up emails or action items from notes/context."""
    data = request.get_json() or {}
    notes = data.get('notes', '')
    title = data.get('title', 'Meeting')

    if not notes:
        return jsonify({'error': 'No notes provided'}), 400

    bot = get_chatbot()
    if not bot:
        return jsonify({'error': 'AI not configured or not available'}), 503

    prompt = f"Based on these meeting notes for '{title}', suggest concise follow-up emails and next steps. Provide a short suggested email draft and a numbered list of next actions. Notes:\n\n{notes}"
    try:
        ai_response = bot.chat(prompt)
        return jsonify({'success': True, 'followups': ai_response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai/translate', methods=['POST'])
@login_required
def ai_translate():
    """Translate provided text into a target language using AI."""
    data = request.get_json() or {}
    text = data.get('text', '')
    target = data.get('target_language', 'en')

    if not text:
        return jsonify({'error': 'No text provided'}), 400

    bot = get_chatbot()
    if not bot:
        return jsonify({'error': 'AI not configured or not available'}), 503

    prompt = f"Translate the following text to {target} while preserving meaning and formatting:\n\n{text}"
    try:
        ai_response = bot.chat(prompt)
        return jsonify({'success': True, 'translation': ai_response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("🌐 Starting Voice Assistant Calendar Web Server...")
    print("📱 Open http://localhost:5000 in your browser")
    app.run(debug=True, host='localhost', port=5000)
