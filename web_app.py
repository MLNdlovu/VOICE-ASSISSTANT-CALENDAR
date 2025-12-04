"""
Web Dashboard for Voice Assistant Calendar
Modern Flask web app with Google Calendar integration, OAuth, and responsive UI.
"""

import os
import json
import secrets
import logging
from datetime import datetime, timedelta, timezone
from functools import wraps
from collections import defaultdict

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory, abort
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")

# IMPORTANT: Allow insecure transport (http) for local development
# In production, ALWAYS use HTTPS
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Import existing modules
import sys
sys.path.insert(0, './src')
import book
import get_details
import voice_handler
import src.recommender as recommender
from src.scheduler_handler import SchedulerCommandHandler, create_scheduler_endpoints
from src.ai.voice_parser import parse_transcript, normalize_transcript
from src.actions.calendar_actions import create_event, get_events, cancel_event
from src.voice_blueprint import voice_bp
# Defer importing the optional AI module to runtime to avoid blocking imports (e.g., when openai is not installed)
initialize_chatbot = None
is_chatgpt_available = lambda: False

# Flask app setup
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(16))

# Configure session security
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('ENV', 'development') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Get OpenAI model from environment
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')

# Voice command logging setup
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    filename='logs/voice.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
voice_logger = logging.getLogger('voice_assistant')

# Rate limiting: track requests per user per minute
rate_limit_tracker = defaultdict(list)
MAX_REQUESTS_PER_MINUTE = 60

def check_rate_limit(user_id: str) -> bool:
    """Check if user has exceeded rate limit (60 requests/minute)"""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=1)
    
    # Clean old requests
    rate_limit_tracker[user_id] = [
        req_time for req_time in rate_limit_tracker[user_id]
        if req_time > cutoff
    ]
    
    # Check limit
    if len(rate_limit_tracker[user_id]) >= MAX_REQUESTS_PER_MINUTE:
        return False
    
    # Add current request
    rate_limit_tracker[user_id].append(now)
    return True

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


# Register blueprints
app.register_blueprint(voice_bp)


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
    """Home page - redirect to dashboard if logged in, else auth page."""
    if 'access_token' in session:
        return redirect(url_for('home'))
    return render_template('auth.html')


@app.route('/auth/oauth-start')
def oauth_start():
    """Initiate OAuth flow."""
    if not CLIENT_SECRET_FILE:
        return "Error: Client secret not configured", 500
    
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('oauth_callback', _external=True)
    )
    
    auth_url, state = flow.authorization_url(prompt='select_account')
    session['oauth_state'] = state
    
    return redirect(auth_url)


@app.route('/login')
def login():
    """Show login/registration page."""
    if 'access_token' in session:
        return redirect(url_for('home'))
    
    if not CLIENT_SECRET_FILE:
        return render_template('auth.html', error="Client secret not configured")
    
    return render_template('auth.html')


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
        
        # After successful OAuth, redirect to the new home dashboard
        return redirect(url_for('home'))
    
    except Exception as e:
        print(f"OAuth error: {e}")
        return f"Authentication failed: {str(e)}", 400


@app.route('/api/complete-profile', methods=['POST'])
@login_required
def complete_profile():
    """Complete user profile with name, surname, and trigger."""
    try:
        data = request.get_json() or {}
        
        session['user_firstname'] = data.get('firstname', 'User').strip()
        session['user_lastname'] = data.get('lastname', '').strip()
        user_trigger = data.get('trigger', 'XX00').strip().upper()
        
        # Validate trigger format - allow flexible triggers: 2-4 letters followed by 1-3 digits
        import re
        if not re.match(r'^[A-Z]{2,4}[0-9]{1,3}$', user_trigger):
            return jsonify({'error': 'Invalid trigger format. Example valid triggers: LN21, VAC20, AB123'}), 400
        
        session['user_trigger'] = user_trigger
        session.modified = True

        # Persist profile to .config/profiles/<email>.json for CLI and background services
        try:
            user_email = session.get('user_email') or data.get('email') or 'unknown'
            profiles_dir = os.path.join('.config', 'profiles')
            os.makedirs(profiles_dir, exist_ok=True)
            profile_path = os.path.join(profiles_dir, f"{user_email}.json")
            profile_data = {
                'firstname': session.get('user_firstname'),
                'lastname': session.get('user_lastname'),
                'trigger': user_trigger,
                'email': user_email
            }
            with open(profile_path, 'w', encoding='utf-8') as pf:
                json.dump(profile_data, pf)
        except Exception as e:
            print(f"Warning: Failed to persist profile: {e}")

        return jsonify({
            'success': True,
            'message': f'Profile completed! Your trigger is {user_trigger}'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/logout')
def logout():
    """Log out user."""
    session.clear()
    return redirect(url_for('login'))


@app.route('/home')
@login_required
def home():
    """New split-screen voice assistant dashboard"""
    return render_template('home.html', user_email=session.get('user_email'))


@app.route('/unified')
@login_required
def unified_dashboard():
    """Redirect to new home page"""
    return redirect(url_for('home'))


@app.route('/ai')
@login_required
def ai_chat():
    """Dedicated AI chat page with premium voice interface."""
    user_email = session.get('user_email', 'User')
    user_name = session.get('user_firstname', 'Welcome')
    user_trigger = session.get('user_trigger', 'XX00')
    # Legacy AI chat page removed - redirect to unified home dashboard
    return redirect(url_for('home'))


@app.route('/register')
def register():
    """Show registration page."""
    if 'access_token' in session:
        return redirect(url_for('home'))
    return render_template('register.html')


@app.route('/api/auth/register', methods=['POST'])
def register_api():
    """Register a new user with local authentication."""
    try:
        from src.auth import AuthManager
        
        data = request.get_json() or {}
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        timezone = data.get('timezone', 'UTC')
        
        if not email or not password:
            return jsonify({'message': 'Email and password are required'}), 400
        
        # Initialize auth manager
        auth_manager = AuthManager(db_path='app.db')
        
        # Register user
        success, message, user = auth_manager.register_user(email, password, timezone)
        
        if not success:
            return jsonify({'message': message}), 400
        
        # Store user info in session
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['timezone'] = user.timezone
        session['is_local_user'] = True
        
        return jsonify({
            'message': 'Registration successful',
            'user_id': user.id,
            'email': user.email
        }), 201
    
    except Exception as e:
        return jsonify({'message': f'Registration error: {str(e)}'}), 500


@app.route('/api/auth/login', methods=['POST'])
def login_api():
    """Login with email and password."""
    try:
        from src.auth import AuthManager
        
        data = request.get_json() or {}
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'message': 'Email and password are required'}), 400
        
        # Initialize auth manager
        auth_manager = AuthManager(db_path='app.db')
        
        # Login user
        success, message, user = auth_manager.login_user(email, password)
        
        if not success:
            return jsonify({'message': message}), 401
        
        # Store user info in session
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['timezone'] = user.timezone
        session['is_local_user'] = True
        
        return jsonify({
            'message': 'Login successful',
            'user_id': user.id,
            'email': user.email,
            'timezone': user.timezone
        }), 200
    
    except Exception as e:
        return jsonify({'message': f'Login error: {str(e)}'}), 500


@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page."""
    # Dashboard template replaced by unified home - redirect to home
    return redirect(url_for('home'))


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

        # Conflict detection: check for overlapping events before creating
        try:
            from src.calendar_conflict import ConflictDetector, TimeSlot
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


@app.route('/api/set-reminder', methods=['POST'])
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
            # Show events for specific day (if date provided) or today
            service = get_calendar_service()
            if not service:
                return jsonify({'error': 'Not authenticated'}), 401
            
            # Get the date to query (default to today)
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
                    event_text = ', '.join(event_summaries)
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


def _fallback_agenda(title, duration=60, participants=None, notes=''):
    participants = participants or []
    agenda = [f"Agenda for: {title}", f"Duration: {duration} minutes", ""]
    agenda.append("1. Welcome & Objectives (5 mins)")
    agenda.append("2. Main Discussion (" + str(max(10, duration - 20)) + " mins)")
    agenda.append("3. Action Items & Owners (10 mins)")
    if participants:
        agenda.append("")
        agenda.append("Participants: " + ', '.join(participants))
    if notes:
        agenda.append("")
        agenda.append("Notes: " + (notes[:300] + ('...' if len(notes) > 300 else '')))
    return '\n'.join(agenda)


def _fallback_actions(notes, title='Meeting'):
    # Very small heuristic: split by sentences and pick ones containing verbs like 'will' or 'please' or 'action'
    import re
    sentences = re.split(r'[\n\.\?\!]+', notes or '')
    actions = []
    for s in sentences:
        s = s.strip()
        if not s: continue
        if any(tok in s.lower() for tok in ['please', 'will', 'action', 'assign', 'todo', 'follow up', 'follow-up']):
            actions.append(s)
        if len(actions) >= 6:
            break
    if not actions:
        # Fallback generic actions
        actions = [f"Follow up on {title}", "Assign owners to key tasks", "Confirm deadlines and next steps"]
    return '\n'.join([f"{i+1}. {a}" for i,a in enumerate(actions)])


def _fallback_email(title, recipients, context=''):
    subj = f"Follow-up: {title}"
    body = f"Hi all,\n\nThanks for attending {title}.\n\nSummary:\n{(context[:400] + ('...' if len(context) > 400 else ''))}\n\nAction items:\n1. Follow up on the items above.\n\nBest regards,\nYour Assistant"
    return subj, body


def _fallback_suggestions(duration, participants, preferred):
    import datetime
    now = datetime.datetime.now()
    suggestions = []
    base = now + datetime.timedelta(days=1)
    times = [10, 14, 16]
    for i in range(3):
        slot_day = base + datetime.timedelta(days=i)
        h = times[i % len(times)]
        start = slot_day.replace(hour=h, minute=0, second=0, microsecond=0)
        suggestions.append(start.isoformat())
    return '\n'.join([f"{i+1}. {s}" for i,s in enumerate(suggestions)])


def _fallback_summarize(notes):
    if not notes:
        return 'No notes provided.'
    short = notes.strip()
    if len(short) > 300:
        short = short[:300].rsplit(' ',1)[0] + '...'
    # try to extract bullets
    bullets = [line.strip() for line in notes.splitlines() if line.strip().startswith('-') or line.strip().startswith('*')]
    summary = short
    if bullets:
        summary += '\n\nAction items:\n' + '\n'.join(bullets[:6])
    return summary


def _fallback_followups(notes, title):
    actions = _fallback_actions(notes, title)
    subj, body = _fallback_email(title, [], notes)
    return f"Suggested email:\nSubject: {subj}\n\n{body}\n\nSuggested actions:\n{actions}"


def _fallback_translate(text, target):
    # Very simple placeholder translation: denote language and return original text.
    return f"[{target}] " + text


@app.route('/api/ai/chat', methods=['POST'])
@login_required
def ai_chat_api():
    """Simple chat/assistant endpoint that forwards user messages to the AI."""
    data = request.get_json() or {}
    message = data.get('message')
    context = data.get('context')
    if not message:
        return jsonify({'error': 'No message provided'}), 400

    bot = get_chatbot()
    if bot:
        try:
            ai_response = bot.chat(message, calendar_context=context)
            return jsonify({'success': True, 'response': ai_response})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    # fallback: simple echo/placeholder
    return jsonify({'success': True, 'response': f"[local] {message}"})


@app.route('/api/ai/project-chat', methods=['POST'])
@login_required
def ai_project_chat():
    """Answer questions about this project using project files as context.

    This endpoint builds a compact project context from `README.md`, `docs/`, and
    key `src/` files (truncated to avoid very large prompts) and sends that
    context together with the user's question to the AI chatbot.
    """
    data = request.get_json() or {}
    message = data.get('message')
    if not message:
        return jsonify({'error': 'No message provided'}), 400

    # Build compact project context
    project_context = build_project_context()

    prompt = (
        "You are an assistant with knowledge of the application codebase. "
        "Use the project context (filenames and short excerpts) to answer the user's question. "
        "If you refer to code, include filename and short line reference.\n\n"
        "Project context:\n" + project_context + "\n\nUser question:\n" + message
    )

    bot = get_chatbot()
    if bot:
        try:
            ai_response = bot.chat(prompt)
            return jsonify({'success': True, 'response': ai_response})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # fallback: simple echo with project hint
    return jsonify({'success': True, 'response': f"[local][project] {message}"})


def build_project_context(max_bytes_per_file: int = 4000) -> str:
    """Collect a compact, truncated view of important project files.

    - Reads `README.md`, top-level `web_app.py`, and files in `src/` and `docs/`.
    - Truncates each file to `max_bytes_per_file` bytes to avoid huge prompts.
    - Returns a concatenated string suitable for inclusion in an AI prompt.
    """
    parts = []
    root = os.path.dirname(__file__)

    # Helper to read safely and truncate
    def read_trunc(path, maxb=max_bytes_per_file):
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                data = fh.read(maxb)
                # If file longer, indicate truncation
                try:
                    fh.seek(0, os.SEEK_END)
                    full_len = fh.tell()
                except Exception:
                    full_len = None
                if full_len and full_len > len(data):
                    data += '\n\n... (truncated) ...'
                return data
        except Exception:
            return ''

    # Always include README.md if available
    readme_path = os.path.join(root, 'README.md')
    if os.path.exists(readme_path):
        parts.append('=== README.md ===\n' + read_trunc(readme_path))

    # Include web_app.py (this file) briefly
    try:
        parts.append('=== web_app.py (main) ===\n' + read_trunc(os.path.join(root, 'web_app.py')))
    except Exception:
        pass

    # Include docs/ markdown files (first few)
    docs_dir = os.path.join(root, 'docs')
    if os.path.isdir(docs_dir):
        for fn in sorted(os.listdir(docs_dir))[:5]:
            if fn.lower().endswith('.md'):
                parts.append(f'=== docs/{fn} ===\n' + read_trunc(os.path.join(docs_dir, fn)))

    # Include key src files (limit count)
    src_dir = os.path.join(root, 'src')
    if os.path.isdir(src_dir):
        for fn in sorted(os.listdir(src_dir))[:8]:
            if fn.endswith('.py'):
                parts.append(f'=== src/{fn} ===\n' + read_trunc(os.path.join(src_dir, fn)))

    # Return joined context (trim overall length)
    full = '\n\n'.join([p for p in parts if p])
    # Final safety cut
    return full[:32000]


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
    prompt = f"Create a structured agenda for a {duration}-minute meeting titled '{title}'. Include sections, time allocations, and brief bullet points. Participants: {', '.join(participants)}. Additional notes: {notes}"
    if bot:
        try:
            ai_response = bot.chat(prompt)
            return jsonify({'success': True, 'agenda': ai_response})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    # fallback
    return jsonify({'success': True, 'agenda': _fallback_agenda(title, duration, participants, notes)})


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
    prompt = f"Extract concise action items from the following meeting notes for '{title}':\n\n{notes}\n\nReturn a numbered list of action items with responsible parties if mentioned." 
    if bot:
        try:
            ai_response = bot.chat(prompt)
            return jsonify({'success': True, 'actions': ai_response})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'success': True, 'actions': _fallback_actions(notes, title)})


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
    prompt = f"Draft a professional email about '{title}'. Recipients: {', '.join(recipients)}. Context: {context}. Include a clear subject line, brief summary, action items, and a polite closing." 
    if bot:
        try:
            ai_response = bot.chat(prompt)
            return jsonify({'success': True, 'email': ai_response})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    subj, body = _fallback_email(title, recipients, context)
    return jsonify({'success': True, 'email': f"Subject: {subj}\n\n{body}"})


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
    prompt = f"Suggest 3 available meeting time slots for a {duration}-minute meeting with participants: {', '.join(participants)}. Preferred days/times: {preferred}. Return ISO local date/time suggestions with brief justification." 
    if bot:
        try:
            ai_response = bot.chat(prompt)
            return jsonify({'success': True, 'suggestions': ai_response})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'success': True, 'suggestions': _fallback_suggestions(duration, participants, preferred)})


@app.route('/api/ai/summarize', methods=['POST'])
@login_required
def ai_summarize():
    """Summarize meeting notes or text using the AI."""
    data = request.get_json() or {}
    notes = data.get('notes', '')
    if not notes:
        return jsonify({'error': 'No notes provided'}), 400

    bot = get_chatbot()
    prompt = f"Please provide a concise meeting summary and action items from the following notes:\n\n{notes}\n\nReturn a short summary and a list of action items." 
    if bot:
        try:
            ai_response = bot.chat(prompt)
            return jsonify({'success': True, 'summary': ai_response})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'success': True, 'summary': _fallback_summarize(notes)})


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
    prompt = f"Based on these meeting notes for '{title}', suggest concise follow-up emails and next steps. Provide a short suggested email draft and a numbered list of next actions. Notes:\n\n{notes}"
    if bot:
        try:
            ai_response = bot.chat(prompt)
            return jsonify({'success': True, 'followups': ai_response})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'success': True, 'followups': _fallback_followups(notes, title)})


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
    prompt = f"Translate the following text to {target} while preserving meaning and formatting:\n\n{text}"
    if bot:
        try:
            ai_response = bot.chat(prompt)
            return jsonify({'success': True, 'translation': ai_response})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'success': True, 'translation': _fallback_translate(text, target)})


@app.route('/api/ai/recommendations', methods=['GET'])
@login_required
def ai_recommendations():
    """Return booking recommendations based on the user's past events."""
    try:
        # Optional query params
        lookback = int(request.args.get('lookback_days', 90))
        max_items = int(request.args.get('max_items', 5))

        service = get_calendar_service()
        if not service:
            return jsonify({'error': 'Not authenticated'}), 401

        recs = recommender.get_recommendations_for_service(service, lookback_days=lookback, max_items=max_items)
        return jsonify({'success': True, 'recommendations': recs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Initialize Smart Scheduler (Optional - for web-first architecture)
# NOTE: Smart Scheduler and optional AI features are disabled for web deployment
scheduler_handler = None
# Uncomment below to enable optional AI scheduler features:
# try:
#     scheduler_handler = SchedulerCommandHandler()
#     create_scheduler_endpoints(app, scheduler_handler)
#     print("[INFO] Smart Scheduler initialized and endpoints registered")
# except Exception as e:
#     print(f"[WARN] Smart Scheduler initialization skipped: {e}")
#     scheduler_handler = None


# ============================================================================
# Voice Assistant API Endpoints
# ============================================================================

# Import voice modules (optional)
# These are not required for the app to run; log a single warning when they are missing.
VOICE_AVAILABLE = False
try:
    from src.voice_engine import VoiceEngine, get_voice_engine, reset_voice_engine
    from src.command_processor import CommandProcessor, CommandType
    from src.calendar_conflict import ConflictDetector, TimeSlot
    from src.conversation_logger import ConversationLogger, ConversationLog
    VOICE_AVAILABLE = True
except Exception as e:  # ImportError or any other import-time error
    # Avoid duplicate warnings when Flask debug reloader imports this module twice.
    # The reloader sets WERKZEUG_RUN_MAIN='true' in the child process. Prefer to log
    # only from the child process, or when not running under the reloader.
    # Only log from the werkzeug reloader child process when in debug mode,
    # or when not running in debug mode at all. This avoids duplicate messages
    # from the reloader parent and child processes.
    flask_debug = os.environ.get('FLASK_DEBUG') in ('1', 'true', 'True')
    is_reloader_child = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    should_log = is_reloader_child or not flask_debug
    if should_log:
        try:
            voice_logger.warning("Optional voice modules unavailable, voice features disabled: %s", e)
        except Exception:
            # Fallback to print if logger isn't available
            print(f"[WARN] Optional voice modules unavailable, voice features disabled: {e}")
    VOICE_AVAILABLE = False

# Global instances
_conversation_logger = None
_command_processor = None


def get_logger():
    """Get or create conversation logger"""
    global _conversation_logger
    if _conversation_logger is None:
        _conversation_logger = ConversationLogger()
    return _conversation_logger


def get_processor():
    """Get or create command processor"""
    global _command_processor
    if _command_processor is None:
        _command_processor = CommandProcessor()
    return _command_processor


@app.route('/api/voice/start', methods=['POST'])
@login_required
def voice_start():
    """Initialize voice assistant session with greeting and trigger phrase"""
    try:
        user_trigger = session.get('user_trigger', 'XX00')
        user_name = session.get('user_firstname', 'User')
        user_id = session.get('user_email', 'unknown')
        
        session_id = f"{user_id}_{int(datetime.now().timestamp())}"
        session['voice_session_id'] = session_id
        session['voice_state'] = 'waiting_for_trigger'  # Track conversation state

        # Default to ephemeral/privacy mode: do not persist or display transcripts
        # This can be toggled by voice command "private mode on" / "private mode off".
        if 'ephemeral_mode' not in session:
            session['ephemeral_mode'] = True

        logger = get_logger()
        logger.start_session(session_id, user_id, device='web')

        # Privacy-preserving greeting (do not reveal trigger)
        greeting_text = f"Hello {user_name}. Voice assistant ready."
        speak_text = f"Hello {user_name}. Voice assistant ready. Say your trigger to activate voice commands."

        return jsonify({
            'success': True,
            'session_id': session_id,
            'user_name': user_name,
            'greeting': greeting_text,
            'speak_text': speak_text,
            'voice_state': 'waiting_for_trigger',
            'ephemeral_mode': session.get('ephemeral_mode', True)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/voice/process-command', methods=['POST'])
@login_required
def voice_process_command():
    """Process voice command with multi-turn conversation state machine"""
    try:
        import time
        start_time = time.time()
        
        data = request.get_json() or {}
        user_text = data.get('text', '').strip()
        
        if not user_text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Get current voice state
        voice_state = session.get('voice_state', 'active')
        user_trigger = session.get('user_trigger', 'XX00')
        user_name = session.get('user_firstname', 'User')
        
        # STATE 1: Waiting for trigger phrase
        if voice_state == 'waiting_for_trigger':
            # Check if user said the trigger phrase (with fuzzy matching)
            if user_text.upper().replace(' ', '').endswith(user_trigger.upper().replace(' ', '')):
                session['voice_state'] = 'active'
                return jsonify({
                    'success': True,
                    'state': 'trigger_detected',
                    'speak_text': 'What can I do for you today?',
                    'message': 'Trigger phrase detected. Listening for commands...',
                    'confidence': 1.0
                })
            else:
                # Trigger not recognized
                return jsonify({
                    'success': False,
                    'state': 'trigger_not_detected',
                    'speak_text': f'I did not recognize that. Please say your trigger phrase: {user_trigger}',
                    'message': f'Please say your trigger phrase: {user_trigger}',
                    'confidence': 0.0
                })
        
        # STATE 2b: Booking in progress - capture meeting time/date
        if voice_state == 'booking_in_progress':
            booking_ctx = session.get('booking_context', {})
            booking_ctx['additional_input'] = user_text
            session['booking_context'] = booking_ctx
            
            # Try to create event with captured info
            try:
                service = get_calendar_service()
                if service:
                    # Parse simple date/time (e.g. "tomorrow at 10am")
                    # For now, use tomorrow at 10am as default if "tomorrow" mentioned
                    start_time_obj = datetime.now(timezone.utc) + timedelta(days=1)
                    
                    # Try to extract hour from text (simple regex)
                    import re as regex_module
                    hour_match = regex_module.search(r'(\d{1,2})\s*(?:am|pm|a\.m|p\.m)', user_text.lower())
                    if hour_match:
                        hour = int(hour_match.group(1))
                        if 'pm' in user_text.lower() and hour < 12:
                            hour += 12
                        start_time_obj = start_time_obj.replace(hour=hour, minute=0, second=0)
                    else:
                        start_time_obj = start_time_obj.replace(hour=10, minute=0, second=0)
                    
                    end_time_obj = start_time_obj + timedelta(minutes=30)
                    
                    event = {
                        'summary': booking_ctx.get('summary', 'Meeting'),
                        'description': f'Voice-booked: {booking_ctx.get("summary")}',
                        'start': {'dateTime': start_time_obj.isoformat(), 'timeZone': 'UTC'},
                        'end': {'dateTime': end_time_obj.isoformat(), 'timeZone': 'UTC'},
                    }
                    
                    created_event = service.events().insert(calendarId='primary', body=event).execute()
                    session['voice_state'] = 'active'
                    return jsonify({
                        'success': True,
                        'command_type': 'book_meeting',
                        'message': f"Meeting booked: {booking_ctx.get('summary')} at {start_time_obj.strftime('%I:%M %p')}",
                        'speak_text': f"Meeting booked for {start_time_obj.strftime('%I:%M %p')}. What else can I help?",
                        'event_id': created_event.get('id')
                    })
            except Exception as e:
                session['voice_state'] = 'active'
                return jsonify({
                    'success': False,
                    'message': f'Failed to book: {str(e)}',
                    'speak_text': 'Could not book that meeting. What else can I do?',
                })
        
        # STATE 2: Active - Process commands
        if voice_state == 'active':
            processor = get_processor()
            command = processor.parse_command(user_text)
            
            response = {
                'success': True,
                'command_type': command.type.value,
                'confidence': command.confidence,
                'parameters': command.parameters,
                'response_time_ms': (time.time() - start_time) * 1000,
                'speak_text': None
            }
            
            # Handle different command types with appropriate responses
            if command.type == CommandType.BOOK_MEETING:
                response['message'] = 'What time would you like to book the meeting?'
                response['speak_text'] = 'What time would you like to book the meeting?'
                session['voice_state'] = 'booking_in_progress'
                session['booking_context'] = {'summary': user_text, 'step': 'waiting_for_time'}
                response['state'] = 'booking_in_progress'
            elif command.type == CommandType.LIST_EVENTS:
                response['message'] = 'Retrieving your calendar events.'
                response['speak_text'] = 'Retrieving your calendar events.'
                response['state'] = 'active'
                # Actually fetch events
                service = get_calendar_service()
                if service:
                    try:
                        now = datetime.now(timezone.utc).isoformat()
                        events_result = service.events().list(
                            calendarId='primary',
                            timeMin=now,
                            maxResults=10,
                            singleEvents=True,
                            orderBy='startTime'
                        ).execute()
                        events = events_result.get('items', [])
                        if events:
                            # Build readable event list
                            event_summaries = []
                            for e in events:
                                title = e.get('summary', 'Untitled')
                                start = e.get('start', {}).get('dateTime') or e.get('start', {}).get('date')
                                if start:
                                    event_summaries.append(f"{title} at {start}")
                                else:
                                    event_summaries.append(title)
                            
                            event_list = ' | '.join(event_summaries[:5])  # Limit to 5 for speech
                            response['speak_text'] = f'You have {len(events)} upcoming events: {event_list}. What else can I help?'
                            response['events'] = events
                            response['message'] = f'Found {len(events)} events'
                        else:
                            response['speak_text'] = 'You have no upcoming events. What can I help you with?'
                    except Exception as e:
                        print(f"Events error: {e}")
                        response['speak_text'] = 'Failed to retrieve events. Please try again.'
                else:
                    response['speak_text'] = 'Calendar service not available.'
            elif command.type == CommandType.SET_REMINDER:
                response['message'] = 'I can set that reminder for you.'
                response['speak_text'] = 'Reminder set. What else can I help?'
                response['state'] = 'active'
            else:
                # Handle stop/deactivate commands
                if any(word in user_text.lower() for word in ['stop', 'stop listening', 'deactivate', 'goodbye']):
                    session['voice_state'] = 'inactive'
                    response['message'] = 'Voice assistant deactivated.'
                    response['speak_text'] = 'Voice assistant deactivated. Say your trigger phrase to reactivate.'
                    response['state'] = 'inactive'
                else:
                    # Attempt to handle unknown/free-form queries with AI if available
                    bot = get_chatbot()
                    if bot:
                        try:
                            ai_reply = bot.chat(user_text)
                            response['success'] = True
                            response['message'] = ai_reply
                            response['speak_text'] = ai_reply
                            response['state'] = 'active'
                        except Exception as e:
                            # Fallback to helpful prompt
                            response['success'] = True
                            response['message'] = 'What would you like to do?'
                            response['speak_text'] = 'I did not catch that. You can book a meeting, see your events, or tell me what you need. What would you like?'
                            response['state'] = 'active'
                    else:
                        # No AI available - provide helpful suggestions
                        response['success'] = True
                        response['message'] = 'What would you like to do?'
                        response['speak_text'] = 'I did not catch that. You can book a meeting, see your events, or tell me what you need. What would you like?'
                        response['state'] = 'active'
            
            return jsonify(response)
        
        # STATE 3: Inactive
        if voice_state == 'inactive':
            return jsonify({
                'success': False,
                'message': 'Voice assistant is inactive. Say your trigger phrase to reactivate.',
                'speak_text': 'Voice assistant is inactive.',
                'state': 'inactive'
            })
        
        return jsonify({'error': 'Unknown voice state'}), 400
    
    except Exception as e:
        print(f"Error processing command: {e}")
        return jsonify({'error': str(e), 'speak_text': 'An error occurred. Please try again.'}), 500


@app.route('/api/voice/end-session', methods=['POST'])
@login_required
def voice_end_session():
    """End voice session"""
    try:
        session_id = session.get('voice_session_id')
        
        if session_id:
            logger = get_logger()
            logger.end_session(session_id)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/voice/save-transcript', methods=['POST'])
@login_required
def save_transcript():
    """Save voice conversation transcript to database"""
    try:
        data = request.get_json() or {}
        
        user_email = session.get('user_email', 'unknown')
        session_id = session.get('voice_session_id', 'unknown')
        transcript = data.get('transcript', [])
        notes = data.get('notes', '')
        ephemeral_mode = session.get('ephemeral_mode', False)
        # If the session is ephemeral, do not persist transcripts to disk
        if ephemeral_mode:
            print(f"Ephemeral mode active for session {session_id}: skipping transcript save")
            return jsonify({
                'success': True,
                'message': 'Ephemeral session - transcript not saved',
                'session_id': session_id,
                'message_count': len(transcript)
            })
        
        # Store transcript data (this would go to a database in production)
        # For now, we'll log it locally
        transcript_data = {
            'user_email': user_email,
            'session_id': session_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'transcript': transcript,
            'notes': notes,
            'message_count': len(transcript)
        }
        
        # Log to console and create entry in .config/conversations/ directory
        try:
            os.makedirs('.config/conversations', exist_ok=True)
            transcript_file = os.path.join('.config/conversations', f"{session_id}.json")
            with open(transcript_file, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, indent=2)
            print(f"Transcript saved: {transcript_file}")
        except Exception as e:
            print(f"Warning: Could not save transcript file: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Transcript saved',
            'session_id': session_id,
            'message_count': len(transcript)
        })
    except Exception as e:
        print(f"Error saving transcript: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/voice/transcript-history', methods=['GET'])
@login_required
def get_transcript_history():
    """Get user's conversation history"""
    try:
        user_email = session.get('user_email', 'unknown')
        days = request.args.get('days', 7, type=int)
        
        history = []
        
        # Read from .config/conversations/ directory
        if os.path.exists('.config/conversations'):
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            for filename in os.listdir('.config/conversations'):
                if not filename.endswith('.json'):
                    continue
                
                try:
                    filepath = os.path.join('.config/conversations', filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Filter by user and date
                    if data.get('user_email') == user_email:
                        timestamp = datetime.fromisoformat(data['timestamp'])
                        if timestamp >= cutoff_date:
                            history.append({
                                'session_id': data['session_id'],
                                'timestamp': data['timestamp'],
                                'message_count': data['message_count'],
                                'notes': data['notes']
                            })
                except Exception as e:
                    print(f"Warning: Could not read transcript {filename}: {e}")
        
        # Sort by timestamp descending
        history.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'success': True,
            'user_email': user_email,
            'days': days,
            'sessions': history,
            'total': len(history)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/voice_cmd', methods=['POST'])
@login_required
def voice_cmd():
    """
    Main voice command endpoint.
    
    Accepts JSON:
    {
      "transcript": "raw text from STT",
      "user_id": "user_id",
      "context": [] (optional, ignored - stateless)
    }
    
    Returns:
    {
      "ok": true/false,
      "assistant_text": "response to speak",
      "spoken_time": "two PM" or null,
      "needs_more_info": true/false,
      "data": { "events": [...] } or null
    }
    """
    try:
        data = request.get_json() or {}
        transcript = data.get('transcript', '').strip()
        user_id = data.get('user_id') or session.get('user_email', 'unknown')
        
        # Check rate limit
        if not check_rate_limit(user_id):
            voice_logger.warning(f"Rate limit exceeded for user {user_id}")
            return jsonify({
                'ok': False,
                'error': 'rate_limit_exceeded',
                'assistant_text': 'You are sending requests too quickly. Please wait a moment.'
            }), 429
        
        # Normalize transcript
        normalized = normalize_transcript(transcript)
        
        # Check for empty transcript
        if not normalized:
            return jsonify({
                'ok': False,
                'error': 'empty_transcript',
                'assistant_text': "I didn't catch that. Please repeat."
            })
        
        # Log the request
        voice_logger.info(f"user_id={user_id}, transcript={normalized}")
        
        # Parse transcript to structured JSON
        parsed = parse_transcript(normalized)
        
        action = parsed.get('action', 'other')
        date_str = parsed.get('date')
        iso_time = parsed.get('iso_time')
        spoken_time = parsed.get('spoken_time')
        title = parsed.get('title')
        confirm_required = parsed.get('confirm_required', False)
        reply = parsed.get('reply', "I'm not sure how to help with that.")
        
        # Log detected action
        voice_logger.info(f"action={action}, confirm_required={confirm_required}")
        
        # Get user timezone (default to UTC)
        user_timezone = session.get('user_timezone', 'UTC')
        
        # Handle actions
        if action == 'book':
            if confirm_required or not title or not date_str or not iso_time:
                # Missing required info - ask for clarification
                return jsonify({
                    'ok': True,
                    'assistant_text': reply,
                    'spoken_time': None,
                    'needs_more_info': True,
                    'data': None
                })
            else:
                # Create event
                result = create_event(
                    user_id=user_id,
                    title=title,
                    date_str=date_str,
                    time_str=iso_time,
                    timezone=user_timezone
                )
                
                if result.get('ok'):
                    return jsonify({
                        'ok': True,
                        'assistant_text': reply,
                        'spoken_time': result.get('spoken_time') or spoken_time,
                        'needs_more_info': False,
                        'data': None
                    })
                else:
                    return jsonify({
                        'ok': False,
                        'assistant_text': result.get('reply', 'Failed to create event.'),
                        'spoken_time': None,
                        'needs_more_info': False,
                        'data': None
                    })
        
        elif action == 'get_events':
            date_to_fetch = date_str or 'today'
            result = get_events(
                user_id=user_id,
                date_str=date_to_fetch,
                timezone=user_timezone
            )
            
            if result.get('ok'):
                events_list = result.get('events', [])
                
                # Build assistant text
                if events_list:
                    event_summaries = ", ".join([f"{e['title']} at {e['spoken_time']}" for e in events_list])
                    assistant_text = f"You have {len(events_list)} events: {event_summaries}"
                else:
                    assistant_text = f"You have no events scheduled for {date_to_fetch}."
                
                return jsonify({
                    'ok': True,
                    'assistant_text': assistant_text,
                    'spoken_time': None,
                    'needs_more_info': False,
                    'data': {'events': events_list}
                })
            else:
                return jsonify({
                    'ok': False,
                    'assistant_text': result.get('reply', 'Could not fetch events.'),
                    'spoken_time': None,
                    'needs_more_info': False,
                    'data': None
                })
        
        elif action == 'cancel':
            # For cancel, we need more info typically
            return jsonify({
                'ok': True,
                'assistant_text': reply,
                'spoken_time': None,
                'needs_more_info': True,
                'data': None
            })
        
        else:  # action == 'other'
            return jsonify({
                'ok': True,
                'assistant_text': reply,
                'spoken_time': spoken_time,
                'needs_more_info': confirm_required,
                'data': None
            })
    
    except Exception as e:
        voice_logger.error(f"Error processing voice command: {e}", exc_info=True)
        return jsonify({
            'ok': False,
            'error': 'internal_error',
            'assistant_text': 'An error occurred processing your request.'
        }), 500


# Internal probe endpoint to verify optional voice modules (no auth required)
@app.route('/internal/voice_probe', methods=['GET'])
def internal_voice_probe():
    """Lightweight probe to check voice module availability and optionally instantiate the engine.
    This endpoint is for local testing and diagnostic use only.
    """
    try:
        info = {'voice_available': VOICE_AVAILABLE}
        if VOICE_AVAILABLE:
            try:
                # Import lazily and instantiate a short-lived engine to verify it works
                from src.voice_engine import get_voice_engine
                engine = get_voice_engine(user_trigger='XX00', user_name='LocalProbe')
                try:
                    state_json = engine.get_state_json()
                except Exception as e:
                    state_json = None
                info['engine_state'] = json.loads(state_json) if state_json else None
            except Exception as e:
                info['engine_error'] = str(e)
        else:
            # Try to import modules to see the real error
            try:
                import importlib
                importlib.import_module('src.voice_engine')
                info['import_probe'] = 'src.voice_engine import succeeded'
            except Exception as e:
                info['import_error'] = str(e)

        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/internal/voice_simulate', methods=['POST'])
def internal_voice_simulate():
    """Simulate the voice flow without requiring authentication.
    Accepts JSON: {"transcript": "text", "user_id": "email@example.com", "timezone": "UTC"}
    This is intended for local testing only and should not be exposed in production.
    """
    try:
        data = request.get_json() or {}
        transcript = data.get('transcript', '').strip()
        user_id = data.get('user_id', data.get('email', 'test@local'))
        user_timezone = data.get('timezone', 'UTC')

        # Determine if this is a demo/simulated request (bypass OAuth/calendar)
        is_demo = False
        try:
            if isinstance(user_id, str) and user_id.endswith('@local'):
                is_demo = True
        except Exception:
            is_demo = bool(data.get('demo', False))

        if not transcript:
            return jsonify({'ok': False, 'error': 'empty_transcript'}), 400

        # Normalize and parse
        normalized = normalize_transcript(transcript)
        parsed = parse_transcript(normalized)

        action = parsed.get('action', 'other')
        date_str = parsed.get('date')
        iso_time = parsed.get('iso_time')
        spoken_time = parsed.get('spoken_time')
        title = parsed.get('title')
        reply = parsed.get('reply', "I'm not sure how to help with that.")

        # Route simulation (defensive handling of non-dict results)
        def _ensure_dict(obj):
            """Ensure we return a dict for downstream code. If obj is a requests.Response,
            try to parse JSON; otherwise convert to string."""
            try:
                # requests.Response has .json() and .text
                import requests as _requests
                if isinstance(obj, _requests.Response):
                    try:
                        return obj.json()
                    except Exception:
                        return {'raw_response': obj.text}
            except Exception:
                pass
            if isinstance(obj, dict):
                return obj
            try:
                return dict(obj)
            except Exception:
                return {'raw': str(obj)}

        if action == 'book':
            # For demo users, try a lightweight fallback parser to extract missing fields
            if is_demo:
                try:
                    import re as _re
                    # infer date keyword
                    if not date_str:
                        if _re.search(r'\btomorrow\b', normalized, _re.I):
                            date_str = 'tomorrow'
                        elif _re.search(r'\btoday\b', normalized, _re.I):
                            date_str = 'today'
                    # infer time (simple HH or H AM/PM)
                    if not iso_time:
                        m = _re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', normalized, _re.I)
                        if m:
                            hour = int(m.group(1))
                            minute = m.group(2) or '00'
                            ampm = (m.group(3) or '').lower()
                            if ampm == 'pm' and hour < 12:
                                hour += 12
                            iso_time = f"{hour:02d}:{int(minute):02d}"
                    # infer title from phrases like 'called NAME' or 'named NAME'
                    if not title:
                        tm = _re.search(r"(?:called|named)\s+([\w\s]+)$", normalized, _re.I)
                        if tm:
                            title = tm.group(1).strip()
                        else:
                            # fallback to first noun phrase after 'book' or 'meeting'
                            tm2 = _re.search(r'(?:book(?: a)?(?: meeting)?|schedule(?: a)?)(?:\s+for)?\s+([\w\s]+)', normalized, _re.I)
                            if tm2:
                                title = tm2.group(1).strip()
                except Exception:
                    pass

                # Clean up inferred title to be human-friendly
                try:
                    if title:
                        # Remove common filler words and trailing time/date fragments
                        cleanup = title
                        # Lowercase for consistent regex matching
                        _lc = cleanup.lower()
                        # Remove phrases like 'tomorrow', 'today', 'at 2 pm', 'at 14:00'
                        cleanup = _re.sub(r"\b(today|tomorrow|tmr)\b", "", cleanup, flags=_re.I)
                        cleanup = _re.sub(r"\bat\s+\d{1,2}(:\d{2})?\s*(am|pm)?\b", "", cleanup, flags=_re.I)
                        # Remove leading verbs like 'book', 'schedule', 'create', 'set'
                        cleanup = _re.sub(r"^(?:book(?: a)?|schedule(?: a)?|create(?: a)?|set(?: a)?)\s+", "", cleanup, flags=_re.I)
                        # Remove connector words commonly left after parsing
                        cleanup = _re.sub(r"\b(called|named)\b", "", cleanup, flags=_re.I)
                        # Remove multiple spaces and punctuation at ends
                        cleanup = cleanup.strip(" .,-\t\n")
                        cleanup = _re.sub(r"\s{2,}", " ", cleanup)
                        # Title case the result for nicer display, limit length
                        cleaned = cleanup.strip()
                        if len(cleaned) > 100:
                            cleaned = cleaned[:100].rsplit(' ', 1)[0] + '...'
                        # Remove consecutive duplicate words ("Meeting Meeting")
                        try:
                            cleaned = _re.sub(r"\b(\w+)(?:\s+\1\b)+", r"\1", cleaned, flags=_re.I)
                        except Exception:
                            pass
                        # Final formatting
                        title = cleaned.title() if cleaned else title
                except Exception:
                    pass

            if not title or not date_str or not iso_time:
                return jsonify({'ok': True, 'assistant_text': reply, 'needs_more_info': True})

            # If this is a demo simulation user, store event locally and return success
            if is_demo:
                try:
                    # Use in-memory voice users DB when available
                    uid = user_id or 'demo@local'
                    _ensure_voice_user(uid)
                    # Resolve simple date keywords if needed
                    from datetime import datetime, timedelta
                    def _resolve_simple(d):
                        if not d: return datetime.utcnow().date().isoformat()
                        dd = str(d).lower()
                        today = datetime.utcnow().date()
                        if dd in ('today', 'tod'):
                            return today.isoformat()
                        if dd in ('tomorrow', 'tmr'):
                            return (today + timedelta(days=1)).isoformat()
                        return d

                    resolved_date = _resolve_simple(date_str)
                    event = {
                        'title': title,
                        'date': resolved_date,
                        'iso_time': iso_time,
                        'spoken_time': spoken_time or iso_time,
                        'created_at': datetime.utcnow().isoformat()
                    }
                    _voice_users_db[uid]['events'].append(event)
                    # Persist demo user changes
                    try:
                        _save_demo_user_to_disk(uid)
                    except Exception:
                        pass
                    return jsonify({'ok': True, 'assistant_text': f'Booked {title} on {resolved_date}', 'result': {'ok': True, 'event': event}})
                except Exception as e:
                    return jsonify({'ok': False, 'assistant_text': f'Failed to create demo event: {e}'}), 500

            raw_result = create_event(
                user_id=user_id,
                title=title,
                date_str=date_str,
                time_str=iso_time,
                timezone=user_timezone
            )
            result = _ensure_dict(raw_result)
            return jsonify({'ok': bool(result.get('ok')), 'assistant_text': reply, 'result': result})

        elif action == 'cancel':
            # Cancel an event (demo mode supports deletion from in-memory demo DB)
            # If not demo, return the assistant reply (which may ask for clarification)
            if is_demo:
                try:
                    uid = user_id or 'demo@local'
                    _ensure_voice_user(uid)
                    # Try to identify matching events
                    import re as _re
                    target_title = title or parsed.get('title') or None
                    # If no title parsed, try to extract from the normalized transcript
                    if not target_title:
                        try:
                            _tmp = _re.sub(r'\bcancel\b', '', normalized, flags=_re.I)
                            _tmp = _re.sub(r'\b(today|tomorrow|tmr|at)\b', '', _tmp, flags=_re.I)
                            _tmp = _re.sub(r'\b(am|pm)\b', '', _tmp, flags=_re.I)
                            _tmp = _re.sub(r'\d{1,2}(:\d{2})?', '', _tmp)
                            _tmp = _tmp.strip(' .,-')
                            if _tmp:
                                target_title = _tmp
                        except Exception:
                            target_title = None
                    # Try to resolve date from parsed value or from keywords in normalized
                    target_date = None
                    try:
                        if date_str:
                            target_date = _resolve_date_keyword(date_str)
                        else:
                            if isinstance(normalized, str) and 'tomorrow' in normalized.lower():
                                from datetime import datetime, timedelta
                                target_date = (datetime.utcnow().date() + timedelta(days=1)).isoformat()
                            elif isinstance(normalized, str) and 'today' in normalized.lower():
                                from datetime import datetime
                                target_date = datetime.utcnow().date().isoformat()
                    except Exception:
                        target_date = None
                    target_time = iso_time or None
                    target_time = iso_time or None

                    events_list = _voice_users_db.get(uid, {}).get('events', [])
                    if not events_list:
                        return jsonify({'ok': False, 'assistant_text': 'No demo events to cancel.'})

                    def _match(ev):
                        # Prefer matching by title or time. Do not match by date alone.
                        ev_title = ev.get('title', '').lower() if ev.get('title') else ''
                        if target_title:
                            tt = str(target_title).lower()
                            if tt in ev_title:
                                return True
                            for w in [x for x in tt.split() if len(x) > 2]:
                                if w in ev_title:
                                    return True
                        # If time provided, match by time
                        if target_time and ev.get('iso_time') == target_time:
                            return True
                        # Date-only matches are too broad for cancellation; require title or time
                        return False

                    removed = []
                    remaining = []
                    for ev in events_list:
                        if _match(ev):
                            removed.append(ev)
                        else:
                            remaining.append(ev)

                    _voice_users_db[uid]['events'] = remaining
                    # Persist demo user changes
                    try:
                        _save_demo_user_to_disk(uid)
                    except Exception:
                        pass

                    if removed:
                        return jsonify({'ok': True, 'assistant_text': f'Removed {len(removed)} event(s).', 'removed': removed})
                    else:
                        # Include debug info to help understand why matching failed
                        try:
                            titles = [ev.get('title') for ev in events_list]
                        except Exception:
                            titles = []
                        return jsonify({'ok': False, 'assistant_text': 'No matching demo events found to cancel.', 'debug': {'target_title': target_title, 'target_date': target_date, 'target_time': target_time, 'events': titles}})
                except Exception as e:
                    return jsonify({'ok': False, 'assistant_text': f'Failed to cancel demo event: {e}'})
            else:
                # Non-demo: return assistant reply (may request clarification)
                return jsonify({'ok': True, 'assistant_text': reply, 'spoken_time': None})

        elif action == 'get_events':
            date_to_fetch = date_str or 'today'
            # Demo mode: return locally stored events without OAuth/calendar access
            if is_demo:
                try:
                    uid = user_id or 'demo@local'
                    _ensure_voice_user(uid)
                    # Resolve date keyword
                    from datetime import datetime, timedelta
                    def _resolve_simple(d):
                        today = datetime.utcnow().date()
                        if not d:
                            return today.isoformat()
                        dd = str(d).lower()
                        if dd in ('today', 'tod'):
                            return today.isoformat()
                        if dd in ('tomorrow', 'tmr'):
                            return (today + timedelta(days=1)).isoformat()
                        return d

                    # If transcript mentions 'tomorrow' or 'today', prefer that over default
                    if (not date_to_fetch or date_to_fetch in ('today', 'tod')) and isinstance(normalized, str):
                        if 'tomorrow' in normalized.lower():
                            date_to_fetch = 'tomorrow'
                        elif 'today' in normalized.lower():
                            date_to_fetch = 'today'
                    resolved = _resolve_simple(date_to_fetch)
                    events = [e for e in _voice_users_db.get(uid, {}).get('events', []) if e.get('date') == resolved]
                    # If no events found, return a small demo set for better UX
                    if not events:
                        sample_time = '14:00'
                        sample_spoken = '2 PM'
                        events = [
                            {'title': 'TestStandup', 'date': resolved, 'iso_time': sample_time, 'spoken_time': sample_spoken},
                            {'title': 'Project Sync', 'date': resolved, 'iso_time': '16:00', 'spoken_time': '4 PM'}
                        ]
                    return jsonify({'ok': True, 'assistant_text': reply, 'events': events})
                except Exception as e:
                    return jsonify({'ok': False, 'assistant_text': f'Could not fetch demo events: {e}', 'debug': {}})

            # Handle cancellation in demo mode: allow deleting stored demo events
            if is_demo and action == 'cancel':
                try:
                    uid = user_id or 'demo@local'
                    _ensure_voice_user(uid)
                    # Try to identify event to cancel by title/date/time
                    target_title = title or parsed.get('title') or None
                    target_date = (date_str and (_resolve_date_keyword(date_str) or date_str)) or None
                    target_time = iso_time or None

                    events_list = _voice_users_db.get(uid, {}).get('events', [])
                    if not events_list:
                        return jsonify({'ok': False, 'assistant_text': 'No demo events to cancel.'})

                    # Find matching events (loose matching)
                    def _match(ev):
                        if target_title and target_title.lower() in ev.get('title', '').lower():
                            return True
                        if target_date and ev.get('date') == target_date:
                            return True
                        if target_time and ev.get('iso_time') == target_time:
                            return True
                        return False

                    removed = []
                    remaining = []
                    for ev in events_list:
                        if _match(ev):
                            removed.append(ev)
                        else:
                            remaining.append(ev)

                    _voice_users_db[uid]['events'] = remaining

                    if removed:
                        return jsonify({'ok': True, 'assistant_text': f'Removed {len(removed)} event(s).', 'removed': removed})
                    else:
                        return jsonify({'ok': False, 'assistant_text': 'No matching demo events found to cancel.'})
                except Exception as e:
                    return jsonify({'ok': False, 'assistant_text': f'Failed to cancel demo event: {e}'})

            raw_result = get_events(user_id=user_id, date_str=date_to_fetch, timezone=user_timezone)
            result = _ensure_dict(raw_result)
            if result.get('ok'):
                events = result.get('events') or []
                return jsonify({'ok': True, 'assistant_text': reply, 'events': events})
            return jsonify({'ok': False, 'assistant_text': result.get('reply', 'Could not fetch events.'), 'debug': result})

        else:
            return jsonify({'ok': True, 'assistant_text': reply, 'spoken_time': spoken_time})

    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/set_trigger', methods=['POST'])
@login_required
def set_trigger():
    """
    Set user's voice trigger phrase.
    
    Accepts JSON:
    {
      "trigger": "voice command phrase"
    }
    
    Returns:
    {
      "ok": true/false
    }
    
    NOTE: Does NOT return the trigger phrase back (privacy)
    """
    try:
        data = request.get_json() or {}
        trigger = data.get('trigger', '').strip()
        user_id = session.get('user_email', 'unknown')
        
        if not trigger:
            return jsonify({'ok': False, 'error': 'empty_trigger'})
        
        # Store trigger in .config/triggers/ directory
        os.makedirs('.config/triggers', exist_ok=True)
        trigger_file = os.path.join('.config/triggers', f"{user_id}.json")
        
        trigger_data = {
            'user_id': user_id,
            'trigger': trigger,
            'set_at': datetime.now(timezone.utc).isoformat()
        }
        
        with open(trigger_file, 'w', encoding='utf-8') as f:
            json.dump(trigger_data, f, indent=2)
        
        voice_logger.info(f"Trigger set for user {user_id}")
        
        # Return success WITHOUT the trigger phrase
        return jsonify({'ok': True})
    
    except Exception as e:
        voice_logger.error(f"Error setting trigger: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/get_trigger_status', methods=['GET'])
@login_required
def get_trigger_status():
    """
    Check if user has set a trigger phrase.
    
    Returns:
    {
      "trigger_set": true/false
    }
    
    NOTE: Does NOT return the actual trigger phrase (privacy)
    """
    try:
        user_id = session.get('user_email', 'unknown')
        trigger_file = os.path.join('.config/triggers', f"{user_id}.json")
        
        trigger_set = os.path.exists(trigger_file)
        
        return jsonify({'trigger_set': trigger_set})
    
    except Exception as e:
        voice_logger.error(f"Error getting trigger status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/voice/transcribe', methods=['POST'])
@login_required
def voice_transcribe():
    """
    Transcribe audio using OpenAI Whisper API.
    
    Accepts JSON:
    {
      "audio": "base64 encoded audio data",
      "format": "wav|mp3|m4a (optional, default: wav)"
    }
    
    Returns:
    {
      "ok": true/false,
      "transcript": "transcribed text",
      "error": "error message if failed"
    }
    """
    try:
        import base64
        import tempfile
        import os as os_module
        
        # Get OpenAI API key from environment
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            return jsonify({
                'ok': False,
                'error': 'openai_not_configured',
                'transcript': '',
                'message': 'OpenAI API key not configured'
            }), 400
        
        data = request.get_json() or {}
        audio_b64 = data.get('audio', '')
        audio_format = data.get('format', 'wav')
        
        if not audio_b64:
            return jsonify({
                'ok': False,
                'error': 'no_audio',
                'transcript': '',
                'message': 'No audio data provided'
            }), 400
        
        # Decode base64 audio
        try:
            audio_bytes = base64.b64decode(audio_b64)
        except Exception as e:
            return jsonify({
                'ok': False,
                'error': 'invalid_audio_encoding',
                'transcript': '',
                'message': f'Failed to decode audio: {str(e)}'
            }), 400
        
        # Create temporary file for audio
        with tempfile.NamedTemporaryFile(suffix=f'.{audio_format}', delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        try:
            # Call Whisper API
            import openai
            openai.api_key = openai_api_key
            
            with open(tmp_path, 'rb') as audio_file:
                transcript_response = openai.Audio.transcribe(
                    model='whisper-1',
                    file=audio_file,
                    language='en'
                )
            
            transcript = transcript_response.get('text', '').strip()
            
            if not transcript:
                return jsonify({
                    'ok': False,
                    'error': 'empty_transcript',
                    'transcript': '',
                    'message': 'Whisper returned empty transcript'
                })
            
            voice_logger.info(f"Transcribed audio: {transcript[:100]}")
            
            return jsonify({
                'ok': True,
                'transcript': transcript,
                'error': None
            })
        
        finally:
            # Clean up temporary file
            try:
                os_module.unlink(tmp_path)
            except Exception:
                pass
    
    except Exception as e:
        voice_logger.error(f"Error transcribing audio: {e}")
        return jsonify({
            'ok': False,
            'error': 'transcription_error',
            'transcript': '',
            'message': str(e)
        }), 500


@app.route('/api/voice/respond', methods=['POST'])
@login_required
def voice_respond():
    """
    Generate voice response using GPT and integrate with TTS.
    
    Accepts JSON:
    {
      "transcript": "user voice command text",
      "context": "optional conversation context"
    }
    
    Returns:
    {
      "ok": true/false,
      "response": "GPT response text",
      "speak_text": "text to be spoken by TTS",
      "error": "error message if failed"
    }
    """
    try:
        data = request.get_json() or {}
        transcript = data.get('transcript', '').strip()
        context = data.get('context', '')
        
        if not transcript:
            return jsonify({
                'ok': False,
                'error': 'no_transcript',
                'response': '',
                'message': 'No transcript provided'
            }), 400
        
        # Get user info for context
        user_email = session.get('user_email', 'unknown')
        user_name = session.get('user_firstname', 'User')
        
        # Build prompt with calendar context
        prompt = f"""You are a helpful voice assistant for a calendar application.
User: {user_name} ({user_email})
Context: {context if context else 'No specific context'}

User said: {transcript}

Respond naturally and concisely as if speaking aloud. Keep responses under 50 words for voice output."""
        
        # Get GPT response
        bot = get_chatbot()
        if bot:
            try:
                gpt_response = bot.chat(prompt)
            except Exception as e:
                voice_logger.warning(f"ChatGPT not available: {e}")
                gpt_response = f"I heard you say: {transcript}. How can I help?"
        else:
            # Fallback if no chatbot available
            gpt_response = f"I heard you say: {transcript}. How can I help?"
        
        voice_logger.info(f"GPT response: {gpt_response[:100]}")
        
        return jsonify({
            'ok': True,
            'response': gpt_response,
            'speak_text': gpt_response,  # Same as response for now
            'error': None
        })
    
    except Exception as e:
        voice_logger.error(f"Error generating response: {e}")
        return jsonify({
            'ok': False,
            'error': 'response_generation_error',
            'response': '',
            'message': str(e)
        }), 500


@app.route('/api/tts', methods=['POST'])
@login_required
def text_to_speech():
    """
    Text-to-Speech endpoint (placeholder for future implementation).
    
    Accepts JSON:
    {
      "text": "text to speak",
      "voice": "optional voice preference"
    }
    
    Returns:
    {
      "ok": true/false,
      "audio_url": "https://..."
    }
    """
    try:
        # Placeholder for future TTS implementation
        return jsonify({
            'ok': False,
            'error': 'not_implemented',
            'message': 'TTS endpoint is not yet implemented. Use browser speechSynthesis API.'
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500




# ============ GPT-5 VOICE ASSISTANT ENDPOINTS ============

@app.route('/api/get_trigger', methods=['GET'])
@login_required
def get_trigger_phrase():
    """
    Get user's trigger phrase for voice activation.
    Returns ONLY the trigger phrase, NOT displayed in UI.
    """
    try:
        trigger = session.get('user_trigger', None)
        
        if not trigger:
            return jsonify({
                'ok': False,
                'error': 'no_trigger_set',
                'message': 'No trigger phrase configured. Set one in Settings.'
            }), 400
        
        return jsonify({
            'ok': True,
            'trigger_phrase': trigger
        })
    except Exception as e:
        voice_logger.error(f"Error getting trigger: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/set_trigger', methods=['POST'])
@login_required
def set_trigger_phrase():
    """
    Save user's trigger phrase for voice activation.
    Trigger is never displayed in UI (password-type input on frontend).
    """
    try:
        data = request.get_json() or {}
        new_trigger = data.get('trigger_phrase', '').strip()
        
        if not new_trigger or len(new_trigger) < 2:
            return jsonify({
                'ok': False,
                'error': 'invalid_trigger',
                'message': 'Trigger phrase must be at least 2 characters'
            }), 400
        
        if len(new_trigger) > 50:
            return jsonify({
                'ok': False,
                'error': 'trigger_too_long',
                'message': 'Trigger phrase must be 50 characters or less'
            }), 400
        
        # Store in session
        session['user_trigger'] = new_trigger.lower().strip()
        session.modified = True
        
        user_email = session.get('user_email', 'unknown')
        voice_logger.info(f"Trigger phrase updated for {user_email}")
        
        return jsonify({
            'ok': True,
            'message': 'Trigger phrase saved successfully'
        })
    except Exception as e:
        voice_logger.error(f"Error setting trigger: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
@login_required
def gpt_chat():
    """
    Chat with OpenAI GPT-5 voice assistant using stateless single-turn conversation.
    Returns only the assistant's reply for the latest message.
    """
    try:
        data = request.get_json() or {}
        message = data.get('message', '').strip()

        if not message:
            return jsonify({
                'ok': False,
                'error': 'empty_message',
                'message': 'Message cannot be empty'
            }), 400
        
        # Rate limiting
        user_id = session.get('user_id', session.get('user_email', 'unknown'))
        if not check_rate_limit(user_id):
            return jsonify({
                'ok': False,
                'error': 'rate_limit',
                'message': 'Too many requests. Try again in a moment.'
            }), 429
        
        # Get OpenAI API key
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return jsonify({
                'ok': False,
                'error': 'no_api_key',
                'message': 'OpenAI API key not configured'
            }), 500
        
        try:
            from openai import OpenAI
        except ImportError:
            return jsonify({
                'ok': False,
                'error': 'openai_not_installed',
                'message': 'OpenAI library not installed. Run: pip install openai'
            }), 500
        
        client = OpenAI(api_key=api_key)
        model = os.environ.get('OPENAI_MODEL', 'gpt-5o-mini')
        
        system_prompt = (
            "You are a friendly and concise voice assistant for a calendar application. "
            "Respond naturally and briefly (max 50 words) suitable for speech output. "
            "Help with calendar actions like booking, canceling, and showing events. "
            "Always respect privacy and avoid disclosing trigger phrases or security details."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        # Single-turn chat completion call
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=200
        )
        
        assistant_message = response.choices[0].message.content.strip()
        
        user_email = session.get('user_email', 'unknown')
        voice_logger.info(f"GPT-5 Chat from {user_email}: {message[:50]}...")
        
        return jsonify({
            'ok': True,
            'response': assistant_message,
            'message': 'Response generated successfully'
        })

    except Exception as e:
        voice_logger.error(f"GPT-5 Chat error: {e}", exc_info=True)
        return jsonify({
            'ok': False,
            'error': 'chat_error',
            'message': 'Sorry, I couldn\'t process that. Try again?'
        }), 500


@app.route('/api/parse_event', methods=['POST'])
@login_required
def parse_event_command():
    """
    Parse voice command to extract event details.
    Uses GPT to understand intent and extract:
    - title: meeting name
    - date: YYYY-MM-DD
    - start_time: HH:MM (24h)
    - end_time: HH:MM (optional)
    - timezone: user's timezone
    - description: optional notes
    - recurrence: optional (daily, weekly, etc.)
    
    Returns null if essential fields are missing.
    """
    try:
        data = request.get_json() or {}
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({
                'ok': False,
                'error': 'empty_command'
            }), 400
        
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return jsonify({
                'ok': False,
                'error': 'no_api_key'
            }), 500
        
        try:
            from openai import OpenAI
        except ImportError:
            return jsonify({
                'ok': False,
                'error': 'openai_not_installed'
            }), 500
        
        client = OpenAI(api_key=api_key)
        model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
        
        # Extract event details using GPT
        system_prompt = '''You are a calendar assistant that extracts event details from natural language.
        
Extract the following from the user's command:
- title: meeting/event name (required)
- date: YYYY-MM-DD format (required, assume today if not specified)
- start_time: HH:MM in 24-hour format (optional)
- end_time: HH:MM (optional)
- timezone: user's timezone (optional)
- description: additional notes (optional)
- recurrence: daily/weekly/monthly if mentioned (optional)

Return ONLY valid JSON like:
{"title": "...", "date": "2025-01-15", "start_time": "14:00", "end_time": "15:00", "timezone": "UTC", "description": "...", "recurrence": null}

If any required field is missing, return null for that field.'''
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f'Extract event details: {command}'}
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        import json
        try:
            event_data = json.loads(response_text)
            
            # Ensure required fields exist
            if not event_data.get('title') or not event_data.get('date'):
                return jsonify({
                    'ok': True,
                    'event': None,
                    'partial': event_data
                })
            
            # Add user's timezone if not specified
            if not event_data.get('timezone'):
                event_data['timezone'] = session.get('timezone', 'UTC')
            
            return jsonify({
                'ok': True,
                'event': event_data
            })
        except json.JSONDecodeError:
            voice_logger.warning(f"Failed to parse event JSON: {response_text}")
            return jsonify({
                'ok': False,
                'error': 'parse_error',
                'raw': response_text
            }), 500
    
    except Exception as e:
        voice_logger.error(f"Event parsing error: {e}")
        return jsonify({
            'ok': False,
            'error': 'parse_error'
        }), 500


@app.route('/api/scheduler', methods=['POST'])
@login_required
def book_event_endpoint():
    """
    Book/schedule an event using parsed event data.
    Accepts:
    {
      "title": "Meeting Name",
      "date": "2025-01-15",
      "start_time": "14:00",
      "end_time": "15:00",
      "timezone": "UTC",
      "description": "optional"
    }
    """
    try:
        data = request.get_json() or {}
        title = data.get('title', '').strip()
        date_str = data.get('date', '').strip()
        start_time = data.get('start_time', '').strip()
        end_time = data.get('end_time', '').strip()
        description = data.get('description', '').strip()
        timezone_str = data.get('timezone', session.get('timezone', 'UTC'))
        
        # Validate required fields
        if not title or not date_str:
            return jsonify({
                'ok': False,
                'error': 'missing_fields',
                'message': 'Title and date are required'
            }), 400
        
        service = get_calendar_service()
        if not service:
            return jsonify({'ok': False, 'error': 'not_authenticated'}), 401
        
        try:
            from datetime import time
            # Parse date and time
            event_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            if start_time:
                start_hour, start_min = map(int, start_time.split(':'))
                start_dt = datetime.combine(event_date, 
                                          time(start_hour, start_min))
            else:
                # Default to 10:00 AM if no time specified
                start_dt = datetime.combine(event_date, time(10, 0))
            
            if end_time:
                end_hour, end_min = map(int, end_time.split(':'))
                end_dt = datetime.combine(event_date, 
                                        time(end_hour, end_min))
            else:
                # Default to 1 hour duration
                end_dt = start_dt + timedelta(hours=1)
            
            # Create event
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': timezone_str
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': timezone_str
                }
            }
            
            result = service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            user_email = session.get('user_email', 'unknown')
            voice_logger.info(f"Event booked by {user_email}: {title} on {date_str}")
            
            return jsonify({
                'ok': True,
                'event_id': result.get('id'),
                'message': f'Event "{title}" booked successfully',
                'event': result
            })
        
        except ValueError as e:
            return jsonify({
                'ok': False,
                'error': 'invalid_date_format',
                'message': f'Invalid date or time format: {e}'
            }), 400
    
    except Exception as e:
        voice_logger.error(f"Booking error: {e}")
        return jsonify({
            'ok': False,
            'error': 'booking_error',
            'message': str(e)
        }), 500







if __name__ == '__main__':
    # Get port from environment variable, default to 5000
    port = int(os.environ.get('PORT', 5000))

    # Avoid non-ASCII emoji output on some Windows consoles
    print("Starting Voice Assistant Calendar Web Server...")
    # Avoid emoji in console output on Windows
    print(f"Open http://localhost:{port} in your browser")
    app.run(debug=True, host='localhost', port=port)
