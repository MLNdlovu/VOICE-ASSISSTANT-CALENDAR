"""
Voice Assistant Calendar - AI-Driven Backend

================================================
ARCHITECTURE: AI IS THE CENTER OF EVERYTHING
================================================

The flow is:
1. User speaks voice command → transcript
2. Transcript goes to AI Interpreter (ai_intent_handler.py)
3. AI decides: intent + parameters
4. Based on intent, execute calendar action
5. Use AI Response Generator to create natural response
6. Speak response back to user

No regex, no pattern matching, no hardcoded rules.
Everything goes through the AI model first.

================================================
"""

import os
import json
import secrets
import logging
import asyncio
from datetime import datetime

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

# Import our AI and calendar modules
import ai_intent_handler
import ai_response
from calendar_service import GoogleCalendarService
import voice_utils

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =====================================================
# FLASK SETUP
# =====================================================

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('FLASK_SECRET', secrets.token_hex(32))
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

CORS(app)

# Unsafe for dev only
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# =====================================================
# GOOGLE OAUTH CONFIG
# =====================================================

SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/calendar'
]

# Find client secret file
CLIENT_SECRET_FILE = None
if os.path.exists('.config'):
    for f in os.listdir('.config'):
        if f.startswith('client_secret') and f.endswith('.json'):
            CLIENT_SECRET_FILE = os.path.join('.config', f)
            break

logger.info(f"🔐 Google OAuth Client Secret: {CLIENT_SECRET_FILE}")

# =====================================================
# GLOBAL CALENDAR SERVICE
# =====================================================

calendar_service = None


def login_required(f):
    """Decorator for protected routes"""
    from functools import wraps
    
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'access_token' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def get_calendar_service() -> GoogleCalendarService:
    """
    Get authenticated Google Calendar service.
    Creates new instance if credentials available.
    
    Returns:
        GoogleCalendarService: Calendar API wrapper
    """
    if 'access_token' not in session:
        return None
    
    try:
        creds = Credentials(
            token=session.get('access_token'),
            refresh_token=session.get('refresh_token')
        )
        service = GoogleCalendarService(CLIENT_SECRET_FILE, creds)
        return service
    except Exception as e:
        logger.error(f"Failed to get calendar service: {str(e)}")
        return None


# =====================================================
# ROUTES - AUTHENTICATION
# =====================================================

@app.route('/')
def index():
    """Home route - redirect to home or login"""
    if 'access_token' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))


@app.route('/login')
def login():
    """Login page"""
    if 'access_token' in session:
        return redirect(url_for('home'))
    return render_template('login.html')


@app.route('/auth/login')
def auth_login():
    """Initiate Google OAuth flow"""
    if not CLIENT_SECRET_FILE:
        return jsonify({'error': 'Google OAuth not configured'}), 500
    
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRET_FILE,
            scopes=SCOPES,
            redirect_uri=url_for('oauth_callback', _external=True)
        )
        auth_url, state = flow.authorization_url(prompt='select_account')
        session['oauth_state'] = state
        
        logger.info(f"🔐 Initiating OAuth flow")
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"OAuth error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/oauth2callback')
def oauth_callback():
    """Handle Google OAuth callback"""
    if not CLIENT_SECRET_FILE:
        return 'Error: Google OAuth not configured', 500
    
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
        
        # Store in session
        session['access_token'] = creds.token
        session['refresh_token'] = creds.refresh_token
        
        # Get user info
        from googleapiclient.discovery import build
        service = build('oauth2', 'v2', credentials=creds)
        user_info = service.userinfo().get().execute()
        session['user_email'] = user_info.get('email')
        
        logger.info(f"✅ User authenticated: {session['user_email']}")
        
        return redirect(url_for('home'))
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return f'Authentication failed: {str(e)}', 400


@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    return redirect(url_for('login'))


# =====================================================
# ROUTES - MAIN APP
# =====================================================

@app.route('/home')
@login_required
def home():
    """Main dashboard"""
    return render_template('index.html', 
                         user_email=session.get('user_email'),
                         debug_mode=os.environ.get('DEBUG', 'True').lower() == 'true')


# =====================================================
# API ROUTES - CALENDAR OPERATIONS
# =====================================================

@app.route('/api/events', methods=['GET'])
@login_required
def get_events():
    """
    Get all events from Google Calendar
    
    Returns:
        {success: bool, events: [...], error: str}
    """
    try:
        service = get_calendar_service()
        if not service:
            return jsonify({'error': 'Calendar service unavailable', 'events': []}), 500
        
        events = service.get_events(max_results=30)
        
        logger.info(f"📅 Retrieved {len(events)} events")
        return jsonify({
            'success': True,
            'events': events,
            'count': len(events)
        })
    
    except Exception as e:
        logger.error(f"Error fetching events: {str(e)}")
        return jsonify({'error': str(e), 'events': []}), 500


# =====================================================
# API ROUTES - AI COMMAND PROCESSING
# =====================================================

@app.route('/api/command', methods=['POST'])
@login_required
def process_command():
    """
    ========================================
    MAIN AI PROCESSING ROUTE
    ========================================
    
    This is where the magic happens:
    
    1. Receive user voice transcript
    2. Send to AI Interpreter (ai_intent_handler.interpret)
    3. AI decides: intent + parameters
    4. Execute action based on intent
    5. Generate natural response (ai_response.generate_response)
    6. Return everything to frontend
    
    Flowchart:
    
    User voice transcript
           ↓
    AI Interpreter (GPT)
           ↓
    {"intent": "create_event", "parameters": {...}}
           ↓
    Route to appropriate action
           ↓
    Execute (create event, delete event, etc.)
           ↓
    AI Response Generator (GPT)
           ↓
    "Your event has been added for..."
           ↓
    Return to frontend + speak
    
    Args (POST JSON):
        {
            "transcript": "book meeting tomorrow at 2pm"
        }
    
    Returns:
        {
            "success": bool,
            "intent": str,
            "parameters": {},
            "ai_response": "Your event has been added...",
            "raw_ai_output": {},  # debug only
            "execution_result": {}  # debug only
        }
    """
    
    try:
        data = request.get_json()
        transcript = data.get('transcript', '').strip()
        
        if not transcript:
            return jsonify({
                'success': False,
                'error': 'No transcript provided',
                'intent': 'error'
            }), 400
        
        logger.info(f"🎤 Processing command: '{transcript}'")
        
        # =====================================================
        # STEP 1: AI INTERPRETATION
        # =====================================================
        # The AI reads the transcript and decides what the user wants
        
        ai_result = asyncio.run(ai_intent_handler.interpret(transcript))
        
        intent = ai_result.get('intent', 'unknown')
        parameters = ai_result.get('parameters', {})
        confidence = ai_result.get('confidence', 0.0)
        
        logger.info(f"🤖 AI decided: intent='{intent}', confidence={confidence:.2f}")
        
        if not ai_result.get('success', False):
            logger.warning(f"⚠️ AI uncertain about intent")
            return jsonify({
                'success': False,
                'intent': intent,
                'error': 'Could not understand command',
                'raw_ai_output': ai_result
            }), 400
        
        # =====================================================
        # STEP 2: EXECUTE COMMAND
        # =====================================================
        # Based on what the AI decided, execute the action
        
        execution_result = _execute_intent(intent, parameters)
        
        # =====================================================
        # STEP 3: GENERATE NATURAL RESPONSE
        # =====================================================
        # Use AI to create a friendly response
        
        ai_response_text = asyncio.run(ai_response.generate_response(
            intent=intent,
            parameters=parameters,
            result=execution_result,
            success=execution_result.get('success', False)
        ))
        
        logger.info(f"💬 AI Response: '{ai_response_text}'")
        
        # =====================================================
        # STEP 4: RETURN TO FRONTEND
        # =====================================================
        
        return jsonify({
            'success': True,
            'intent': intent,
            'parameters': parameters,
            'confidence': confidence,
            'ai_response': ai_response_text,
            'execution_result': execution_result,
            # Debug info (only in dev mode)
            'debug': {
                'raw_ai_output': ai_result,
                'debug_mode': os.environ.get('DEBUG', 'False').lower() == 'true'
            }
        })
    
    except Exception as e:
        logger.error(f"Error processing command: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'intent': 'error'
        }), 500


def _execute_intent(intent: str, parameters: dict) -> dict:
    """
    Execute the action based on AI-determined intent.
    
    This is where the AI's decision is turned into action.
    
    Args:
        intent (str): "create_event", "delete_event", "show_events"
        parameters (dict): Intent-specific parameters
    
    Returns:
        dict: Execution result with success status and details
    """
    
    try:
        service = get_calendar_service()
        if not service:
            return {'success': False, 'error': 'Calendar service unavailable'}
        
        # =====================================================
        # CREATE EVENT
        # =====================================================
        if intent == 'create_event':
            title = parameters.get('title', 'Untitled')
            date = parameters.get('date')
            time = parameters.get('time', '09:00')
            duration = parameters.get('duration', 60)
            
            if not date:
                return {'success': False, 'error': 'No date provided'}
            
            # Validate date/time
            if not voice_utils.is_valid_date(date) or not voice_utils.is_valid_time(time):
                return {'success': False, 'error': 'Invalid date or time format'}
            
            logger.info(f"📝 Creating event: '{title}' on {date} at {time}")
            
            result = service.create_event(
                title=title,
                date=date,
                time=time,
                duration=duration
            )
            
            if result:
                return {
                    'success': True,
                    'event_id': result['id'],
                    'event_title': title,
                    'event_date': date,
                    'event_time': time,
                    'message': f"✅ Created event '{title}'"
                }
            else:
                return {'success': False, 'error': 'Failed to create event'}
        
        # =====================================================
        # DELETE EVENT
        # =====================================================
        elif intent == 'delete_event':
            event_title = parameters.get('event_title', '')
            
            if not event_title:
                return {'success': False, 'error': 'No event title provided'}
            
            logger.info(f"🗑️ Deleting event: '{event_title}'")
            
            # Find event by title
            event = service.find_event_by_title(event_title)
            
            if not event:
                return {'success': False, 'error': f"Event '{event_title}' not found"}
            
            success = service.delete_event(event['id'])
            
            if success:
                return {
                    'success': True,
                    'event_id': event['id'],
                    'event_title': event['title'],
                    'message': f"✅ Deleted event '{event['title']}'"
                }
            else:
                return {'success': False, 'error': 'Failed to delete event'}
        
        # =====================================================
        # SHOW EVENTS
        # =====================================================
        elif intent == 'show_events':
            date_range = parameters.get('date_range', 'today')
            
            logger.info(f"📅 Fetching events for: {date_range}")
            
            events = service.get_events()
            
            return {
                'success': True,
                'event_count': len(events),
                'events': events,
                'message': f"✅ Found {len(events)} events"
            }
        
        # =====================================================
        # UNKNOWN INTENT
        # =====================================================
        else:
            logger.warning(f"⚠️ Unknown intent: {intent}")
            return {
                'success': False,
                'error': f"Unknown intent: {intent}"
            }
    
    except Exception as e:
        logger.error(f"Error executing intent: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


# =====================================================
# ERROR HANDLING
# =====================================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {str(e)}")
    return jsonify({'error': 'Server error'}), 500


# =====================================================
# STARTUP
# =====================================================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🚀 Voice Assistant Calendar - AI Powered")
    logger.info("=" * 60)
    logger.info("AI Integration: ✅ Enabled")
    logger.info(f"OpenAI Model: {os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')}")
    logger.info(f"Debug Mode: {os.environ.get('DEBUG', 'True')}")
    logger.info("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('FLASK_RUN_PORT', 5000)),
        debug=os.environ.get('DEBUG', 'True').lower() == 'true'
    )
