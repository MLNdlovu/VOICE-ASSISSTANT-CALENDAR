"""
Main Flask Application for Voice Assistant Calendar
Registers all blueprints and handles application setup
"""

import os
import json
import secrets
import logging
from datetime import datetime, timedelta, timezone
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

# Import blueprints
from src.auth_blueprint import auth_bp
from src.calendar_blueprint import calendar_bp
from src.voice_blueprint import voice_bp
from src.ai_blueprint import ai_bp

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
app.register_blueprint(auth_bp)
app.register_blueprint(calendar_bp)
app.register_blueprint(voice_bp)
app.register_blueprint(ai_bp)

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

if __name__ == '__main__':
    # Get port from environment variable, default to 5000
    port = int(os.environ.get('PORT', 5000))

    # Avoid non-ASCII emoji output on some Windows consoles
    print("Starting Voice Assistant Calendar Web Server...")
    # Avoid emoji in console output on Windows
    print(f"Open http://localhost:{port} in your browser")
    app.run(debug=True, host='localhost', port=port)
