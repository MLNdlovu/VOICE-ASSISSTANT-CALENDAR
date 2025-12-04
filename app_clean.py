"""
Voice Assistant Calendar - Clean Flask Backend
Minimal setup with Google Calendar integration and OpenAI
"""

import os
import json
import secrets
from datetime import datetime, timedelta

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Initialize Flask
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(16))
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Google OAuth config
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/calendar'
]

CLIENT_SECRET_FILE = None
for f in os.listdir('.config'):
    if f.startswith('client_secret') and f.endswith('.json'):
        CLIENT_SECRET_FILE = os.path.join('.config', f)
        break

# OpenAI
try:
    import openai
    openai.api_key = os.environ.get('OPENAI_API_KEY')
    HAS_OPENAI = bool(openai.api_key)
except:
    HAS_OPENAI = False


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'access_token' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def get_calendar_service():
    """Get authenticated Google Calendar service"""
    if 'access_token' not in session:
        return None
    try:
        creds = Credentials(token=session.get('access_token'))
        return build('calendar', 'v3', credentials=creds)
    except:
        return None


# ROUTES

@app.route('/')
def index():
    if 'access_token' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))


@app.route('/login')
def login():
    if 'access_token' in session:
        return redirect(url_for('home'))
    return render_template('login.html')


@app.route('/auth/login')
def auth_login():
    if not CLIENT_SECRET_FILE:
        return jsonify({'error': 'Client secret not configured'}), 500
    
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('oauth_callback', _external=True)
    )
    auth_url, state = flow.authorization_url(prompt='select_account')
    session['oauth_state'] = state
    return redirect(auth_url)


@app.route('/oauth2callback')
def oauth_callback():
    if not CLIENT_SECRET_FILE:
        return 'Error: Client secret not configured', 500
    
    try:
        state = session.get('oauth_state')
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRET_FILE,
            scopes=SCOPES,
            state=state,
            redirect_uri=url_for('oauth_callback', _external=True)
        )
        flow.fetch_token(authorization_response=request.url)
        creds = flow.credentials
        
        session['access_token'] = creds.token
        session['refresh_token'] = creds.refresh_token
        
        # Get user info
        service = build('oauth2', 'v2', credentials=creds)
        user_info = service.userinfo().get().execute()
        session['user_email'] = user_info.get('email')
        
        return redirect(url_for('home'))
    except Exception as e:
        return f'Authentication failed: {str(e)}', 400


@app.route('/home')
@login_required
def home():
    return render_template('home.html', user_email=session.get('user_email'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# API ROUTES

@app.route('/api/get_events')
@login_required
def get_events():
    """Get all events from Google Calendar"""
    try:
        service = get_calendar_service()
        if not service:
            return jsonify({'error': 'Calendar service unavailable'}), 500
        
        now = datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=20,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = []
        for event in events_result.get('items', []):
            start = event['start'].get('dateTime', event['start'].get('date'))
            events.append({
                'id': event['id'],
                'title': event.get('summary', 'Untitled'),
                'start': start,
                'date': start.split('T')[0] if 'T' in start else start,
                'time': start.split('T')[1][:5] if 'T' in start else '00:00'
            })
        
        return jsonify({'events': events, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e), 'events': []}), 200


@app.route('/api/book_event', methods=['POST'])
@login_required
def book_event():
    """Create event on Google Calendar"""
    try:
        data = request.get_json()
        title = data.get('title', 'Untitled')
        date = data.get('date')
        time = data.get('time', '09:00')
        
        if not date:
            return jsonify({'error': 'Date required'}), 400
        
        service = get_calendar_service()
        if not service:
            return jsonify({'error': 'Calendar service unavailable'}), 500
        
        # Create event
        event = {
            'summary': title,
            'start': {
                'dateTime': f"{date}T{time}:00",
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': f"{date}T{int(time.split(':')[0])+1}:{time.split(':')[1]}:00",
                'timeZone': 'UTC'
            }
        }
        
        created_event = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        
        return jsonify({
            'success': True,
            'event_id': created_event['id'],
            'message': f"Event '{title}' created!"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/delete_event', methods=['DELETE'])
@login_required
def delete_event():
    """Delete event from Google Calendar"""
    try:
        data = request.get_json()
        event_id = data.get('event_id')
        
        if not event_id:
            return jsonify({'error': 'Event ID required'}), 400
        
        service = get_calendar_service()
        if not service:
            return jsonify({'error': 'Calendar service unavailable'}), 500
        
        service.events().delete(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        return jsonify({'success': True, 'message': 'Event deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/parse_event', methods=['POST'])
@login_required
def parse_event():
    """Parse voice command using OpenAI GPT"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        if not HAS_OPENAI:
            return jsonify({
                'success': False,
                'message': 'OpenAI not configured. Please set OPENAI_API_KEY.'
            }), 501
        
        # Call OpenAI
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[{
                'role': 'system',
                'content': 'Extract event title, date (YYYY-MM-DD), and time (HH:MM) from user speech. Return JSON: {"title": "...", "date": "...", "time": "..."}. If incomplete, ask clarification.'
            }, {
                'role': 'user',
                'content': text
            }],
            temperature=0.3,
            max_tokens=200
        )
        
        result_text = response['choices'][0]['message']['content']
        
        try:
            event = json.loads(result_text)
            return jsonify({
                'success': True,
                'event': {
                    'title': event.get('title', 'Untitled'),
                    'date': event.get('date', ''),
                    'time': event.get('time', '09:00')
                }
            })
        except:
            return jsonify({
                'success': False,
                'message': result_text
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
