"""
Authentication Blueprint for Voice Assistant Calendar
Handles OAuth, login, registration, and user management
"""

import os
import json
import secrets
import logging
from datetime import timedelta
from functools import wraps
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, abort
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")

# IMPORTANT: Allow insecure transport (http) for local development
# In production, ALWAYS use HTTPS
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Import existing auth module
try:
    from src.auth import AuthManager
except ImportError:
    AuthManager = None

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

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/')
def index():
    """Home page - redirect to dashboard if logged in, else auth page."""
    if 'access_token' in session:
        return redirect(url_for('calendar.unified_dashboard'))
    return render_template('auth.html')

@auth_bp.route('/auth/oauth-start')
def oauth_start():
    """Initiate OAuth flow."""
    if not CLIENT_SECRET_FILE:
        return "Error: Client secret not configured", 500

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('auth.oauth_callback', _external=True)
    )

    auth_url, state = flow.authorization_url(prompt='select_account')
    session['oauth_state'] = state

    return redirect(auth_url)

@auth_bp.route('/login')
def login():
    """Show login/registration page."""
    if 'access_token' in session:
        return redirect(url_for('calendar.unified_dashboard'))

    if not CLIENT_SECRET_FILE:
        return render_template('auth.html', error="Client secret not configured")

    return render_template('auth.html')

@auth_bp.route('/oauth/callback')
def oauth_callback():
    """Handle OAuth callback."""
    if not CLIENT_SECRET_FILE:
        return "Error: Client secret not configured", 500

    state = session.get('oauth_state')
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=url_for('auth.oauth_callback', _external=True)
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

        # Check for registration data in query params or show profile completion page
        return render_template('oauth_callback.html')

    except Exception as e:
        print(f"OAuth error: {e}")
        return f"Authentication failed: {str(e)}", 400

@auth_bp.route('/api/complete-profile', methods=['POST'])
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

@auth_bp.route('/logout')
def logout():
    """Log out user."""
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/register')
def register():
    """Show registration page."""
    if 'access_token' in session:
        return redirect(url_for('calendar.unified_dashboard'))
    return render_template('register.html')

@auth_bp.route('/api/auth/register', methods=['POST'])
def register_api():
    """Register a new user with local authentication."""
    try:
        if not AuthManager:
            return jsonify({'message': 'Authentication system not available'}), 500

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

@auth_bp.route('/api/auth/login', methods=['POST'])
def login_api():
    """Login with email and password."""
    try:
        if not AuthManager:
            return jsonify({'message': 'Authentication system not available'}), 500

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

@auth_bp.route('/api/user', methods=['GET'])
@login_required
def get_user():
    """Get current user info."""
    return jsonify({
        'email': session.get('user_email'),
        'authenticated': True
    })
