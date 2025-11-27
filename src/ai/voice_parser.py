"""
Voice command parser - sends transcript to Hugging Face for NLU processing
"""

import json
import os
import requests
from typing import Dict, Any

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '').strip()
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
HF_API_KEY = os.getenv("HF_API_KEY", "").strip()
HF_API_URL = "https://api-inference.huggingface.co/models/mistral/Mistral-7B-Instruct-v0.2"

try:
    if OPENAI_API_KEY:
        import openai
        openai.api_key = OPENAI_API_KEY
except Exception:
    # openai may not be installed or key invalid; we'll fall back below
    openai = None

def parse_transcript(transcript: str) -> Dict[str, Any]:
    """
    Send transcript to Hugging Face inference API for command parsing.

    Returns structured JSON with:
    - action: "book", "get_events", "cancel", "chat", "other"
    - date: "YYYY-MM-DD" or relative phrase, or null for non-calendar actions
    - iso_time: "HH:MM" or None
    - spoken_time: natural English time or None
    - title: event name or None
    - confirm_required: bool
    - reply: assistant text
    """
    
    if not transcript or not transcript.strip():
        return {
            "action": "other",
            "date": None,
            "iso_time": None,
            "spoken_time": None,
            "title": None,
            "confirm_required": False,
            "reply": "I didn't catch that. Please repeat."
        }
    
    # Prefer OpenAI if configured, otherwise try Hugging Face, otherwise fallback.
    # Load parser prompt
    prompt_file = os.path.join(
        os.path.dirname(__file__),
        "..",
        "prompts",
        "parser_prompt.txt"
    )

    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            system_prompt = f.read()
    except Exception as e:
        print(f"Warning: Could not load parser prompt: {e}")
        system_prompt = "Parse the user's voice command into JSON with keys: action, date, iso_time, spoken_time, title, confirm_required, reply. Use 'chat' for general conversations."
    
    # 1) Try OpenAI via HTTP API if API key set
    if OPENAI_API_KEY:
        try:
            oa_headers = {
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': 'application/json'
            }
            oa_payload = {
                'model': OPENAI_MODEL,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': transcript}
                ],
                'temperature': 0.0,
                'max_tokens': 300
            }
            oa_resp = requests.post('https://api.openai.com/v1/chat/completions', json=oa_payload, headers=oa_headers, timeout=15)
            oa_resp.raise_for_status()
            oa_json = oa_resp.json()
            text = ''
            try:
                text = oa_json['choices'][0]['message']['content']
            except Exception:
                text = str(oa_json)

            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                try:
                    parsed = json.loads(text[json_start:json_end])
                    for field in ["action", "date", "iso_time", "spoken_time", "title", "confirm_required", "reply"]:
                        if field not in parsed:
                            parsed[field] = None
                    return parsed
                except Exception:
                    pass
        except Exception as e:
            print(f"OpenAI parsing error: {e}")

    # 2) Try Hugging Face if configured
    if HF_API_KEY:
        payload = {
            "inputs": f"{system_prompt}\n\nUser input: {transcript}",
            "parameters": {
                "max_new_tokens": 200,
                "temperature": 0.3,
                "top_p": 0.9
            }
        }
        headers = {
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(HF_API_URL, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            result = None
            try:
                result = response.json()
            except Exception:
                # fallback to text
                text = response.text
                result = {'generated_text': text}

            # Extract generated text
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get("generated_text", "")
            else:
                generated_text = result.get("generated_text", "")

            json_start = generated_text.find('{')
            json_end = generated_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                try:
                    parsed = json.loads(generated_text[json_start:json_end])
                    for field in ["action", "date", "iso_time", "spoken_time", "title", "confirm_required", "reply"]:
                        if field not in parsed:
                            parsed[field] = None
                    return parsed
                except Exception:
                    return _fallback_parse(transcript)
        except requests.exceptions.RequestException as e:
            print(f"Error calling Hugging Face API: {e}")

    # Final fallback
    return _fallback_parse(transcript)


def _fallback_parse(transcript: str) -> Dict[str, Any]:
    """
    Fallback parsing when HF API is not available.
    Uses simple keyword matching to detect intent.
    """
    transcript_lower = transcript.lower()
    
    # Detect booking intent
    if any(word in transcript_lower for word in ['book', 'schedule', 'create', 'meeting', 'appointment']):
        return {
            "action": "book",
            "date": None,
            "iso_time": None,
            "spoken_time": None,
            "title": transcript,
            "confirm_required": True,
            "reply": "I can help you book a meeting. What time and date would you like?"
        }
    
    # Detect list events intent
    if any(word in transcript_lower for word in ['show', 'list', 'what', 'events', 'calendar', 'schedule']):
        return {
            "action": "get_events",
            "date": "today",
            "iso_time": None,
            "spoken_time": None,
            "title": None,
            "confirm_required": False,
            "reply": "Let me fetch your events for today."
        }
    
    # Detect cancel intent
    if any(word in transcript_lower for word in ['cancel', 'delete', 'remove']):
        return {
            "action": "cancel",
            "date": None,
            "iso_time": None,
            "spoken_time": None,
            "title": None,
            "confirm_required": True,
            "reply": "Which event would you like to cancel?"
        }
    
    # Default to chat
    return {
        "action": "other",
        "date": None,
        "iso_time": None,
        "spoken_time": None,
        "title": None,
        "confirm_required": False,
        "reply": f"I understood: {transcript}"
    }


def normalize_transcript(transcript: str) -> str:
    """Normalize transcript: lowercase, trim whitespace"""
    return transcript.strip().lower() if transcript else ""

