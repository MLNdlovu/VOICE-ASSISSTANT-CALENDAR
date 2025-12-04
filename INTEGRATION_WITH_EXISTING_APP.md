# Integration Guide: Adding Clean UI to Existing web_app.py

If you want to keep your current `web_app.py` and just update the UI, follow this guide.

## ✅ Step 1: Update Templates

Replace your template files:

- **DELETE**: `templates/voice_demo.html` (old)
- **DELETE**: `templates/ai_chat.html` (old)
- **DELETE**: `templates/dashboard.html` (old)
- **DELETE**: `templates/unified_dashboard.html` (old)

- **UPDATE**: `templates/home.html` ← Use the new one (ready!)
- **KEEP**: `templates/login.html`, `templates/auth.html`, `templates/oauth_callback.html`

---

## ✅ Step 2: Update Static Files

Replace:
- `static/css/style.css` ← Use the new one (ready!)
- `static/js/assistant.js` ← Use the new one (ready!)

Delete old files:
- `static/voice-assistant.js`
- `static/voice-gpt.js`
- `static/voice-interface.js`
- `static/voice.js`
- `static/voice-animations.css`
- `static/app.js`
- `static/accessibility.js`

---

## ✅ Step 3: Update web_app.py Routes

Find the `@app.route('/unified')` section and update it:

```python
# BEFORE (old):
@app.route('/unified')
@login_required
def unified_dashboard():
    """Redirect to voice demo (simplified interface for demo)"""
    if 'voice_state' not in session:
        session['voice_state'] = 'active'
    if 'booking_context' not in session:
        session['booking_context'] = {}
    
    user_name = session.get('user_firstname', 'Welcome')
    return render_template('voice_demo.html', user_name=user_name)


# AFTER (new):
@app.route('/home')
@login_required
def home():
    """New split-screen voice assistant dashboard"""
    return render_template('home.html', user_email=session.get('user_email'))


@app.route('/unified')
@login_required
def unified_dashboard():
    """Redirect to new home page"""
    return redirect(url_for('home'))
```

---

## ✅ Step 4: Ensure Required API Routes

Make sure these routes exist in web_app.py:

```python
@app.route('/api/get_events')
@login_required
def get_events():
    """Get all calendar events"""
    # Should return: {'events': [...], 'success': True}
    # Each event: {id, title, start, date, time}
    pass

@app.route('/api/book_event', methods=['POST'])
@login_required
def book_event():
    """Create calendar event"""
    # Input: {'title': '...', 'date': 'YYYY-MM-DD', 'time': 'HH:MM'}
    # Should return: {'success': True, 'event_id': '...'}
    pass

@app.route('/api/delete_event', methods=['DELETE'])
@login_required
def delete_event():
    """Delete calendar event"""
    # Input: {'event_id': '...'}
    # Should return: {'success': True}
    pass

@app.route('/api/parse_event', methods=['POST'])
@login_required
def parse_event():
    """Parse voice command with OpenAI GPT"""
    # Input: {'text': 'book meeting tomorrow at 2pm'}
    # Should return: {
    #     'success': True,
    #     'event': {'title': '...', 'date': 'YYYY-MM-DD', 'time': 'HH:MM'}
    # }
    pass
```

---

## ✅ Step 5: Update Login Redirect

Find where users are redirected after OAuth callback, usually in `/oauth/callback` or `/oauth2callback`:

```python
# BEFORE:
return redirect(url_for('unified_dashboard'))

# AFTER:
return redirect(url_for('home'))
```

Also update the login page (`/`) redirect:

```python
# BEFORE:
@app.route('/')
def index():
    if 'access_token' in session:
        return redirect(url_for('unified_dashboard'))
    return render_template('auth.html')

# AFTER:
@app.route('/')
def index():
    if 'access_token' in session:
        return redirect(url_for('home'))
    return render_template('auth.html')
```

---

## ✅ Step 6: Optional - Clean Up Unused Routes

You can now delete these old routes (if your app has them):

```python
# DELETE THESE:
@app.route('/ai')
def ai_chat():
    ...

@app.route('/dashboard')
def dashboard():
    ...

@app.route('/api/voice_cmd')
def voice_cmd():  # Old voice route
    ...

# And any other experimental routes
```

---

## ✅ Step 7: Test

```bash
# Restart Flask
python web_app.py

# Navigate to
http://localhost:5000

# Should redirect to /home with new split-screen UI
```

---

## 🔄 Summary of Changes

| File | Action | Status |
|------|--------|--------|
| `templates/home.html` | Create new | ✅ Ready |
| `static/css/style.css` | Replace | ✅ Ready |
| `static/js/assistant.js` | Replace | ✅ Ready |
| `web_app.py` | Add `/home` route | 📝 Manual |
| `web_app.py` | Update redirects | 📝 Manual |
| Old templates | Delete | 📝 Manual |
| Old JS/CSS | Delete | 📝 Manual |

---

## ⚠️ Important: API Requirements

The new `static/js/assistant.js` expects these API endpoints to exist and work correctly:

1. **`GET /api/get_events`**
   - Returns list of calendar events
   - Must include: `id`, `title`, `start`, `date`, `time`

2. **`POST /api/book_event`**
   - Creates new calendar event
   - Expects: `title`, `date`, `time`

3. **`DELETE /api/delete_event`**
   - Deletes calendar event
   - Expects: `event_id`

4. **`POST /api/parse_event`**
   - Parses voice text with OpenAI
   - Expects: `text`
   - Returns: `success`, `event` object OR `message`

If any are missing, the UI will show error messages. Make sure these are implemented!

---

## 🎯 Quick Test

After integration:

1. Click "🎤 Talk to Assistant"
2. Say: "hey assistant, book meeting tomorrow at 2pm"
3. Expect: Event created + right panel updated

If it doesn't work:
- Check browser console (F12) for errors
- Check Flask logs for server errors
- Verify all 4 API routes return proper JSON

---

## 📝 Notes

- The new UI is **completely separate** from your existing code
- It uses the same Google Calendar API (no conflicts)
- The same authentication system (OAuth sessions)
- No changes to `.env` or configuration needed (except OPENAI_API_KEY if not set)
- Fully backward compatible with your current backend

---

Need help? Check `CLEAN_REWRITE_GUIDE.md` for detailed documentation.
