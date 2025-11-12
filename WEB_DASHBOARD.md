# Voice Assistant Calendar - Web Dashboard

A modern, responsive web interface for managing your Google Calendar with voice integration, built with Flask.

## Features

- 🌐 **Web Dashboard** – Access your calendar from any browser
- 📱 **Responsive Design** – Works on desktop, tablet, and mobile
- 🔐 **Google OAuth** – Secure login with your Google account
- 📅 **Event Management** – View, book, and cancel events
- ⚙️ **Settings Panel** – Configure timezone and default durations
- 🎤 **Voice Integration** – Ready for voice commands (via GUI app)
- 🔄 **Real-time Updates** – See events as they're added

## Getting Started

### Prerequisites

- Python 3.11+
- Flask installed (included in `requirements-voice.txt`)
- Google Calendar API credentials (`.config/client_secret_*.json`)

### Installation

1. **Install Flask dependencies:**
   ```bash
   pip install Flask>=2.3.0 Werkzeug>=2.3.0
   ```

2. **Or install all requirements:**
   ```bash
   pip install -r requirements-voice.txt
   ```

### Running the Web App

1. **Start the Flask server:**
   ```bash
   python web_app.py
   ```

   You should see:
   ```
   🌐 Starting Voice Assistant Calendar Web Server...
   📱 Open http://localhost:5000 in your browser
   ```

2. **Open your browser and navigate to:**
   ```
   http://localhost:5000
   ```

3. **Sign in with your Google account** – the app will handle OAuth authentication

4. **Start managing your calendar!**

## Usage

### Dashboard Tabs

#### 📅 My Events
- View all upcoming events
- See event details (time, description)
- Cancel events with one click

#### ➕ Book Event
- Create new events with:
  - Event title
  - Date (with date picker)
  - Time
  - Duration (15-480 minutes)
  - Description (optional)
- Events are added to your primary Google Calendar

#### ⚙️ Settings
- Change your timezone
- Set default event duration
- Manage settings across sessions

## API Endpoints

The web app exposes REST API endpoints for calendar operations:

### Events
- `GET /api/events` – Get all upcoming events
- `POST /api/book` – Create a new event
  ```json
  {
    "summary": "Meeting Title",
    "date": "2025-03-23",
    "time": "10:00",
    "duration": 60,
    "description": "Optional description"
  }
  ```
- `DELETE /api/cancel/<event_id>` – Cancel an event

### Settings
- `GET /api/settings` – Get user settings
- `POST /api/settings` – Update settings
  ```json
  {
    "timezone": "Africa/Johannesburg",
    "default_event_duration": 30
  }
  ```

### User
- `GET /api/user` – Get current user info

### Auth
- `GET /login` – Start OAuth login
- `GET /oauth/callback` – OAuth callback (handled automatically)
- `GET /logout` – Sign out

## Project Structure

```
.
├── web_app.py                    # Flask app & API routes
├── templates/
│   └── dashboard.html           # Main UI template
├── static/
│   ├── app.js                   # Frontend JavaScript
│   └── style.css                # Responsive styles
├── requirements-voice.txt       # Python dependencies
└── .config/
    └── client_secret_*.json     # Google OAuth credentials
```

## Integration with GUI App

The web app and GUI share the same backend:
- Both use the same Google Calendar API
- Settings are stored in `.config/gui_settings.json`
- Can run simultaneously on different ports

**Run both:**
```bash
# Terminal 1: GUI
python voice_assistant_calendar.py

# Terminal 2: Web Dashboard
python web_app.py
```

## Deployment Options

### Local Network (LAN)
```bash
python web_app.py --host 0.0.0.0 --port 5000
```
Then access from other computers: `http://<your-ip>:5000`

### Cloud Deployment

#### Heroku
```bash
heroku login
heroku create your-app-name
git push heroku main
```

#### PythonAnywhere
1. Upload files to PythonAnywhere
2. Create a web app with Flask
3. Configure with your client secret

#### DigitalOcean / AWS
1. Deploy Flask app to server
2. Set up nginx as reverse proxy
3. Use SSL/TLS for HTTPS

## Environment Variables

Optional configuration via environment:

```bash
export FLASK_SECRET_KEY="your-secret-key"
export FLASK_ENV="production"
export FLASK_DEBUG=0
```

## Troubleshooting

**"Client secret not found"**
- Ensure `client_secret_*.json` exists in `.config/`
- Check file permissions

**"Not authenticated"**
- Clear browser cookies and sign in again
- Check that OAuth tokens are valid

**"Port 5000 already in use"**
- Change port: `python web_app.py --port 5001`
- Or kill existing process: `lsof -i :5000` (macOS/Linux)

## License

This project is part of Voice Assistant Calendar. See main README for details.

## Support

For issues or feature requests, check the main project GitHub or documentation.
