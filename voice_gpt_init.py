"""
Integration script to add voice GPT endpoints to Flask app
Run this after importing Flask app
"""

import os
import json
from datetime import datetime, timedelta
from flask import request, jsonify, session

# Initialize voice GPT endpoints for Flask
def setup_voice_gpt_endpoints(app):
    """
    Register all GPT-based voice assistant endpoints with Flask app
    Call this after creating the Flask app instance
    """
    
    # In-memory user storage (replace with DB in production)
    users_db = {}
    
    def get_user_id():
        """Get current user ID from session"""
        return session.get('user_id', '1')
    
    def ensure_user_exists(uid):
        """Initialize user entry if doesn't exist"""
        if uid not in users_db:
            users_db[uid] = {
                'email': session.get('user_email', 'demo@local'),
                'trigger': None,
                'events': [],
                'history': []
            }
        return users_db[uid]
    
    def parse_with_llm(transcript_text):
        """Parse voice command using OpenAI GPT"""
        try:
            from openai import OpenAI
        except ImportError:
            return {
                'action': 'other',
                'reply': 'OpenAI not installed. Run: pip install openai'
            }
        
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return {
                    'action': 'other',
                    'reply': 'OpenAI API key not configured.'
                }
            
            client = OpenAI(api_key=api_key)
            model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            
            prompt = f'''You are a strict calendar parser. Respond ONLY with valid JSON.
Input: "{transcript_text}"

Return JSON with these exact keys:
- action: "book" | "get_events" | "cancel" | "other"
- date: "YYYY-MM-DD" or "today" or "tomorrow" or null
- iso_time: "HH:MM" (24h format) or null
- spoken_time: friendly time like "two PM" or null
- title: event title string or null
- confirm_required: boolean (true if missing info)
- reply: string (ask for missing fields or answer if action=other)

Example: {{"action":"book","date":"today","iso_time":"14:00","spoken_time":"two PM","title":"Meeting","confirm_required":false,"reply":""}}

RESPOND ONLY WITH VALID JSON, NO OTHER TEXT.'''
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {'role': 'system', 'content': 'You are a JSON-only parser.'},
                    {'role': 'user', 'content': prompt}
                ],
                temperature=0,
                max_tokens=300
            )
            
            content = response.choices[0].message.content.strip()
            return json.loads(content)
        
        except Exception as e:
            app.logger.error(f'Parse error: {e}')
            return {
                'action': 'other',
                'reply': "Sorry, I couldn't parse that."
            }
    
    def chat_with_llm(text):
        """Simple chat response using OpenAI"""
        try:
            from openai import OpenAI
        except ImportError:
            return "OpenAI not available."
        
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return "API key not configured."
            
            client = OpenAI(api_key=api_key)
            model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a helpful calendar assistant. Keep responses brief (under 50 words) for voice output. Be friendly.'
                    },
                    {'role': 'user', 'content': text}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            app.logger.error(f'Chat error: {e}')
            return "Sorry, I couldn't reach AI right now."
    
    def resolve_date_keyword(date_str):
        """Convert date keywords to ISO format"""
        if not date_str:
            return None
        
        d = str(date_str).lower().strip()
        today = datetime.utcnow().date()
        
        if d in ('today', 'tod'):
            return today.isoformat()
        if d == 'tomorrow':
            return (today + timedelta(days=1)).isoformat()
        
        # Check if already ISO format (YYYY-MM-DD)
        try:
            if len(d) == 10 and d[4] == '-' and d[7] == '-':
                return d
        except:
            pass
        
        return d
    
    # ============ ROUTE: GET TRIGGER ============
    @app.route('/api/get_trigger', methods=['GET'])
    def api_get_trigger():
        """Get trigger status (returns only boolean, never the actual phrase)"""
        try:
            uid = get_user_id()
            user = ensure_user_exists(uid)
            return jsonify({'trigger_set': bool(user.get('trigger'))})
        except Exception as e:
            app.logger.error(f'Error getting trigger: {e}')
            return jsonify({'trigger_set': False}), 500
    
    # ============ ROUTE: SET TRIGGER ============
    @app.route('/api/set_trigger', methods=['POST'])
    def api_set_trigger():
        """Save trigger phrase (server stores, never returns it)"""
        try:
            uid = get_user_id()
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
    
    # ============ ROUTE: VOICE COMMAND ============
    @app.route('/api/voice_cmd', methods=['POST'])
    def api_voice_cmd():
        """Process voice command: parse intent, route action, return response"""
        try:
            uid = get_user_id()
            user = ensure_user_exists(uid)
            
            data = request.json or {}
            transcript = (data.get('transcript') or '').strip()
            
            if not transcript:
                return jsonify({
                    'ok': False,
                    'reply': "I didn't catch that. Please repeat."
                }), 400
            
            app.logger.info(f'Voice command from {uid}: {transcript[:50]}...')
            
            # Parse command using LLM
            parsed = parse_with_llm(transcript)
            action = parsed.get('action', 'other')
            
            # ---- HANDLE: GET_EVENTS ----
            if action == 'get_events':
                date = resolve_date_keyword(parsed.get('date'))
                # Strict date filtering - only events on this specific date
                events = [e for e in user['events'] if e.get('date') == date]
                
                if events:
                    details = ', '.join([
                        f"{e.get('title', '(no title)')} at {e.get('spoken_time', e.get('iso_time', 'unknown'))}"
                        for e in events
                    ])
                    count = len(events)
                    assistant_text = f"You have {count} event{'s' if count != 1 else ''} on {date}: {details}."
                else:
                    assistant_text = f"You have no events on {date}."
                
                return jsonify({
                    'ok': True,
                    'assistant_text': assistant_text,
                    'data': events
                })
            
            # ---- HANDLE: BOOK ----
            elif action == 'book':
                if parsed.get('confirm_required'):
                    return jsonify({
                        'ok': True,
                        'assistant_text': parsed.get('reply', 'Please provide more details.'),
                        'needs_more_info': True
                    })
                
                # Verify we have at least title and date
                title = parsed.get('title')
                date = resolve_date_keyword(parsed.get('date'))
                
                if not title or not date:
                    missing = []
                    if not title:
                        missing.append('event name')
                    if not date:
                        missing.append('date')
                    
                    return jsonify({
                        'ok': True,
                        'assistant_text': f"I need a {' and '.join(missing)}. Please say again.",
                        'needs_more_info': True
                    })
                
                # Create event
                event = {
                    'title': title,
                    'date': date,
                    'iso_time': parsed.get('iso_time'),
                    'spoken_time': parsed.get('spoken_time'),
                    'created_at': datetime.utcnow().isoformat()
                }
                
                user['events'].append(event)
                
                # Build confirmation message
                reply = f"✓ Booked '{event['title']}' on {event['date']}"
                if event['spoken_time']:
                    reply += f" at {event['spoken_time']}"
                reply += "."
                
                return jsonify({
                    'ok': True,
                    'assistant_text': reply,
                    'data': event
                })
            
            # ---- HANDLE: OTHER (general chat) ----
            else:
                reply = chat_with_llm(transcript)
                user['history'].append({
                    'user': transcript,
                    'assistant': reply
                })
                
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
