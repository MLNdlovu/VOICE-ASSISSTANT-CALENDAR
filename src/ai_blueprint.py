"""
AI Blueprint for Voice Assistant Calendar
Handles AI chat, agenda generation, action items, email drafting, and other AI-powered features
"""

import os
import json
from flask import Blueprint, request, jsonify, session, redirect, url_for
from datetime import datetime, timezone

ai_bp = Blueprint('ai', __name__)

def login_required(f):
    """Decorator to require login."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Global chatbot instance
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

@ai_bp.route('/api/ai/chat', methods=['POST'])
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

@ai_bp.route('/api/ai/project-chat', methods=['POST'])
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
    root = os.path.dirname(os.path.dirname(__file__))

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

@ai_bp.route('/api/ai/agenda', methods=['POST'])
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

@ai_bp.route('/api/ai/actions', methods=['POST'])
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

@ai_bp.route('/api/ai/email', methods=['POST'])
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

@ai_bp.route('/api/ai/suggest-times', methods=['POST'])
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

@ai_bp.route('/api/ai/summarize', methods=['POST'])
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

@ai_bp.route('/api/ai/followups', methods=['POST'])
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

@ai_bp.route('/api/ai/translate', methods=['POST'])
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

@ai_bp.route('/api/ai/recommendations', methods=['GET'])
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
