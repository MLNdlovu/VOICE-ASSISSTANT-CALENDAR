"""
Web Dashboard for Voice Assistant Calendar
Modern Flask web app with Google Calendar integration, OAuth, and responsive UI.
"""

import os
import json
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Import existing modules
import book
import get_details
import voice_handler

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
            return jsonify({'success': True, 'event_id': created})
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
        if command == 'book':
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
                return jsonify({
                    'success': True,
                    'command': command,
                    'message': f'✅ Event booked: {summary} on {date} at {time}',
                    'event_id': created
                })
            else:
                return jsonify({'error': 'Failed to create event', 'command': command}), 500
        
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
                return jsonify({
                    'success': True,
                    'command': command,
                    'message': f'✅ Event cancelled on {date} at {time}'
                })
            else:
                return jsonify({'error': 'Event not found', 'command': command}), 404
        
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
            return jsonify({
                'success': True,
                'command': command,
                'events': events,
                'message': f'You have {len(events)} upcoming events'
            })
        
        elif command == 'help':
            # Show available commands
            return jsonify({
                'success': True,
                'command': command,
                'message': 'Available commands: book, cancel-book, events, help, share, config, exit'
            })
        
        elif command == 'share':
            # Calendar sharing instructions
            return jsonify({
                'success': True,
                'command': command,
                'message': 'Share your calendar by opening Google Calendar settings and adding collaborators.'
            })
        
        else:
            # Unknown command
            return jsonify({
                'success': False,
                'command': command,
                'message': f'Unknown command: {voice_text}. Try "book", "cancel", "events", or "help"'
            }), 400
    
    except Exception as e:
        return jsonify({'error': str(e), 'type': 'exception'}), 500


if __name__ == '__main__':
    print("🌐 Starting Voice Assistant Calendar Web Server...")
    print("📱 Open http://localhost:5000 in your browser")
    app.run(debug=True, host='localhost', port=5000)
