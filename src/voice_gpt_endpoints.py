"""
GPT-based voice assistant endpoints for Flask
Handles trigger management, voice command parsing, event creation, and chat
"""

import os
import json
from datetime import datetime, timedelta
from flask import request, jsonify, session

# Initialize OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

def init_voice_endpoints(app, get_user_func=None):
    """
    Register voice assistant endpoints with Flask app
    
    Args:
        app: Flask application instance
        get_user_func: Optional function to get current user (defaults to session-based)
    """
    
    # Default user getter using sessions
    def default_get_user():
        uid = session.get('user_id', '1')
        return uid
    
    get_user = get_user_func or default_get_user
    
    # In-memory user storage (replace with DB in production)
    users_db = {}
    
    def ensure_user_exists(uid):
        if uid not in users_db:
            users_db[uid] = {
                'email': session.get('user_email', 'demo@local'),
                'trigger': None,
                'events': [],
                'history': []
            }
        return users_db[uid]
    
    # ============ TRIGGER MANAGEMENT ============
    
    @app.route('/api/get_trigger', methods=['GET'])
    def api_get_trigger():
        """Get trigger status (returns only bool, not the actual trigger)"""
        try:
            uid = get_user()
            user = ensure_user_exists(uid)
            return jsonify({'trigger_set': bool(user.get('trigger'))})
        except Exception as e:
            app.logger.error(f'Error getting trigger: {e}')
            return jsonify({'trigger_set': False}), 500
    
    @app.route('/api/set_trigger', methods=['POST'])
    def api_set_trigger():
        """Save trigger phrase (never returned to client)"""
        try:
            uid = get_user()
            user = ensure_user_exists(uid)
            
            data = request.json or {}
            trigger = (data.get('trigger') or '').strip().lower()
            
            if not trigger or len(trigger) < 2:
                return jsonify({'ok': False, 'error': 'invalid_trigger'}), 400
            
            if len(trigger) > 50:
                return jsonify({'ok': False, 'error': 'trigger_too_long'}), 400
            
            user['trigger'] = trigger
            app.logger.info(f'Trigger set for user {uid}')
            
            return jsonify({'ok': True})
        except Exception as e:
            app.logger.error(f'Error setting trigger: {e}')
            return jsonify({'ok': False, 'error': str(e)}), 500
    
    # ============ VOICE COMMAND PROCESSING ============
    
    def parse_with_llm(transcript_text):
        """Parse voice command using OpenAI to extract intent and fields"""
        if not OPENAI_AVAILABLE:
            return {
                'action': 'other',
                'reply': 'AI parsing not available. OpenAI not configured.'
            }
        
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return {
                    'action': 'other',
                    'reply': 'AI service not configured.'
                }
            
            client = OpenAI(api_key=api_key)
            model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            
            prompt = f'''You are a strict calendar parser. Respond ONLY with JSON.
Input: "{transcript_text}"

Return JSON with these keys:
- action: "book" | "get_events" | "cancel" | "other"
- date: "YYYY-MM-DD" or "today" or "tomorrow" or null
- iso_time: "HH:MM" (24h) or null
- spoken_time: friendly time like "two PM" or null
- title: event title or null
- confirm_required: true if missing info, false otherwise
- reply: if confirm_required=true, ask user for missing fields; if action=other, provide helpful response

Example output: {{"action":"book","date":"today","iso_time":"14:00","spoken_time":"two PM","title":"Meeting","confirm_required":false,"reply":""}}

Return ONLY valid JSON, no other text.'''
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {'role': 'system', 'content': 'You are a JSON-only parser. Respond ONLY with valid JSON.'},
                    {'role': 'user', 'content': prompt}
                ],
                temperature=0,
                max_tokens=300
            )
            
            content = response.choices[0].message.content.strip()
            parsed = json.loads(content)
            return parsed
        
        except Exception as e:
            app.logger.error(f'Parse error: {e}')
            return {
                'action': 'other',
                'reply': "Sorry, I couldn't parse that."
            }
    
    def chat_with_llm(text):
        """Simple chat response using OpenAI"""
        if not OPENAI_AVAILABLE:
            return "I'm not connected to AI right now."
        
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return "AI service not configured."
            
            client = OpenAI(api_key=api_key)
            model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a helpful calendar assistant. Keep responses brief (under 50 words) for voice output. Be friendly and helpful.'
                    },
                    {'role': 'user', 'content': text}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            app.logger.error(f'Chat error: {e}')
            return "Sorry, I couldn't reach the AI right now."
    
    def resolve_date_keyword(date_str):
        """Convert date keywords to ISO format"""
        if not date_str:
            return None
        
        d = date_str.lower().strip()
        today = datetime.utcnow().date()
        
        if d in ('today', 'tod'):
            return today.isoformat()
        if d == 'tomorrow':
            return (today + timedelta(days=1)).isoformat()
        
        # Check if already ISO format
        try:
            if len(d) == 10 and d[4] == '-' and d[7] == '-':
                return d
        except:
            pass
        
        return d
    
    @app.route('/api/voice_cmd', methods=['POST'])
    def api_voice_cmd():
        """Process voice command: parse, route, and respond"""
        try:
            uid = get_user()
            user = ensure_user_exists(uid)
            
            data = request.json or {}
            transcript = (data.get('transcript') or '').strip()
            
            if not transcript:
                return jsonify({
                    'ok': False,
                    'reply': "I didn't catch that. Please repeat."
                }), 400
            
            app.logger.info(f'Command from {uid}: {transcript[:50]}...')
            
            # Parse command intent
            parsed = parse_with_llm(transcript)
            action = parsed.get('action', 'other')
            
            # ---- HANDLE GET_EVENTS ----
            if action == 'get_events':
                date = resolve_date_keyword(parsed.get('date'))
                # Filter events for this specific date
                events = [e for e in user['events'] if e.get('date') == date]
                
                if events:
                    details = ', '.join([
                        f"{e.get('title', '(no title)')} at {e.get('spoken_time', e.get('iso_time', 'unknown time'))}"
                        for e in events
                    ])
                    assistant_text = f"You have {len(events)} event{'s' if len(events) != 1 else ''} on {date}: {details}."
                else:
                    assistant_text = f"You have no events on {date}."
                
                return jsonify({
                    'ok': True,
                    'assistant_text': assistant_text,
                    'data': events
                })
            
            # ---- HANDLE BOOK ----
            elif action == 'book':
                if parsed.get('confirm_required'):
                    return jsonify({
                        'ok': True,
                        'assistant_text': parsed.get('reply', 'Please provide more details.'),
                        'needs_more_info': True
                    })
                
                # Create event
                event = {
                    'title': parsed.get('title') or 'Untitled Event',
                    'date': resolve_date_keyword(parsed.get('date')),
                    'iso_time': parsed.get('iso_time'),
                    'spoken_time': parsed.get('spoken_time'),
                    'created_at': datetime.utcnow().isoformat()
                }
                
                if not event['date']:
                    return jsonify({
                        'ok': True,
                        'assistant_text': "I need a date. When would you like to schedule this?",
                        'needs_more_info': True
                    })
                
                user['events'].append(event)
                
                reply = f"✓ Booked '{event['title']}' on {event['date']}"
                if event['spoken_time']:
                    reply += f" at {event['spoken_time']}"
                reply += "."
                
                return jsonify({
                    'ok': True,
                    'assistant_text': reply,
                    'data': event
                })
            
            # ---- HANDLE OTHER (general chat) ----
            else:
                reply = chat_with_llm(transcript)
                user['history'].append({'user': transcript, 'assistant': reply})
                
                return jsonify({
                    'ok': True,
                    'assistant_text': reply
                })
        
        except Exception as e:
            app.logger.error(f'Voice command error: {e}')
            return jsonify({
                'ok': False,
                'reply': 'Sorry, something went wrong.'
            }), 500

if __name__ == '__main__':
    # This module should be imported, not run directly
    pass
