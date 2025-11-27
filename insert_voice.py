#!/usr/bin/env python3
"""
Script to add voice GPT endpoints to web_app.py
Run from the project root directory
"""

import os

def insert_voice_endpoints():
    """Insert voice endpoints before the if __name__ block"""
    
    # Read current file with UTF-8 encoding
    with open('web_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find insertion point
    if_name_pos = content.find("if __name__ == '__main__':")
    if if_name_pos == -1:
        print("ERROR: Could not find if __name__ block")
        return False
    
    # Voice endpoints code
    voice_code = '''

# ============ GPT-BASED VOICE ASSISTANT ENDPOINTS ============
_voice_users_db = {}

def _get_voice_user_id():
    return session.get("user_id", "1")

def _ensure_voice_user(uid):
    if uid not in _voice_users_db:
        _voice_users_db[uid] = {"email": session.get("user_email", "demo"), "trigger": None, "events": [], "history": []}
    return _voice_users_db[uid]

def _parse_with_llm(transcript_text):
    try:
        from openai import OpenAI
    except ImportError:
        return {"action": "other", "reply": "OpenAI not installed"}
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"action": "other", "reply": "No API key"}
        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        prompt = f"""You are a calendar parser. Respond ONLY with JSON.
Input: "{transcript_text}"
Return: {{"action":"book|get_events|other","date":"YYYY-MM-DD or today","iso_time":"HH:MM","spoken_time":"2 PM","title":"...","confirm_required":false,"reply":""}}"""
        response = client.chat.completions.create(model=model,messages=[{"role":"system","content":"JSON only"},{"role":"user","content":prompt}],temperature=0,max_tokens=300)
        return json.loads(response.choices[0].message.content.strip())
    except Exception as e:
        app.logger.error(f"Parse: {e}")
        return {"action":"other","reply":"Could not parse"}

def _chat_with_llm(text):
    try:
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key: return "No API key"
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(model=os.getenv("OPENAI_MODEL","gpt-4o-mini"),messages=[{"role":"system","content":"Calendar assistant. Brief."},{"role":"user","content":text}],temperature=0.3,max_tokens=300)
        return response.choices[0].message.content.strip()
    except:
        return "AI unavailable"

def _resolve_date_keyword(date_str):
    if not date_str: return None
    d = str(date_str).lower().strip()
    today = datetime.utcnow().date()
    if d in ("today","tod"): return today.isoformat()
    if d == "tomorrow": return (today + timedelta(days=1)).isoformat()
    try:
        if len(d)==10 and d[4]=="-" and d[7]=="-": return d
    except: pass
    return d

@app.route("/api/get_trigger", methods=["GET"])
def api_get_trigger():
    try:
        uid = _get_voice_user_id()
        user = _ensure_voice_user(uid)
        return jsonify({"trigger_set": bool(user.get("trigger"))})
    except Exception as e:
        app.logger.error(f"Trigger: {e}")
        return jsonify({"trigger_set": False}), 500

@app.route("/api/set_trigger", methods=["POST"])
def api_set_trigger():
    try:
        uid = _get_voice_user_id()
        user = _ensure_voice_user(uid)
        data = request.json or {}
        trigger = (data.get("trigger") or "").strip().lower()
        if not trigger or len(trigger)<2: return jsonify({"ok":False}), 400
        user["trigger"] = trigger
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"ok":False}), 500

@app.route("/api/voice_cmd", methods=["POST"])
def api_voice_cmd():
    try:
        uid = _get_voice_user_id()
        user = _ensure_voice_user(uid)
        data = request.json or {}
        transcript = (data.get("transcript") or "").strip()
        if not transcript: return jsonify({"ok":False,"reply":"I didn't catch that"}), 400
        parsed = _parse_with_llm(transcript)
        action = parsed.get("action","other")
        if action=="get_events":
            date = _resolve_date_keyword(parsed.get("date"))
            events = [e for e in user["events"] if e.get("date")==date]
            text = f"You have {len(events)} event(s) on {date}." if events else f"No events on {date}."
            return jsonify({"ok":True,"assistant_text":text,"data":events})
        elif action=="book":
            if parsed.get("confirm_required"): return jsonify({"ok":True,"assistant_text":parsed.get("reply"),"needs_more_info":True})
            title = parsed.get("title")
            date = _resolve_date_keyword(parsed.get("date"))
            if not title or not date: return jsonify({"ok":True,"assistant_text":"Need title and date","needs_more_info":True})
            event = {"title":title,"date":date,"iso_time":parsed.get("iso_time"),"spoken_time":parsed.get("spoken_time"),"created_at":datetime.utcnow().isoformat()}
            user["events"].append(event)
            reply = f"Booked {event['title']} on {event['date']}."
            return jsonify({"ok":True,"assistant_text":reply,"data":event})
        else:
            reply = _chat_with_llm(transcript)
            return jsonify({"ok":True,"assistant_text":reply})
    except Exception as e:
        app.logger.error(f"Voice: {e}")
        return jsonify({"ok":False,"reply":"Error"}), 500

'''
    
    # Insert code
    new_content = content[:if_name_pos] + voice_code + '\n' + content[if_name_pos:]
    
    # Write back with UTF-8 encoding
    with open('web_app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✓ Voice endpoints added successfully to web_app.py")
    return True

if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__) or '.')
    insert_voice_endpoints()
