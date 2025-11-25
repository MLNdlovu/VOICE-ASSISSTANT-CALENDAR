# ✅ PRE-DEPLOYMENT SETUP GUIDE

**Status**: Ready to Deploy  
**Date**: November 25, 2025  
**System Completion**: 92%

---

## 🚨 CRITICAL SETUP (DO THIS FIRST)

### Step 1: Create `.env` File
```bash
# In project root directory
cp .env.template .env

# Edit .env and fill in REQUIRED variables:
```

**Required Variables** (must fill these):
```env
# CRITICAL - Generate new secret key
FLASK_SECRET_KEY=<generate-with-python-c-import-secrets-print-secrets-token-hex-32>

# CRITICAL - Get from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-<your-actual-key-here>

# Environment
ENV=production    # or development

# Optional but recommended
OPENAI_MODEL=gpt-3.5-turbo
DATABASE_PATH=app.db
```

**How to Generate FLASK_SECRET_KEY**:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
# Copy the output and paste into .env
```

---

### Step 2: Add Google OAuth Credentials
```bash
# 1. Download from: https://console.cloud.google.com/
# 2. Go to: APIs & Services > Credentials
# 3. Download OAuth 2.0 Client ID (JSON)
# 4. Rename to: client_secret_XXXXXXXXX.json
# 5. Place in .config/ directory

# Verify:
ls -la .config/client_secret_*.json
# Should show your file exists
```

---

### Step 3: Install Dependencies
```bash
# Create virtual environment (if not already done)
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

# Install all packages
pip install -r requirements-voice.txt

# Verify installation
pip list | grep -E "flask|google|openai"
```

---

### Step 4: Initialize Database
```bash
# Create SQLite database with schema
python -c "from src.auth import AuthManager; AuthManager()"

# Verify database created
ls -la app.db

# Should show file exists and has size > 0
```

---

### Step 5: Verify Configuration
```bash
# Run quick test to verify everything loads
python -c "
import os
from dotenv import load_dotenv

load_dotenv()

checks = {
    'FLASK_SECRET_KEY': bool(os.environ.get('FLASK_SECRET_KEY')),
    'OPENAI_API_KEY': bool(os.environ.get('OPENAI_API_KEY')),
    'Database': os.path.exists('app.db'),
    'OAuth Config': any(f.startswith('client_secret_') for f in os.listdir('.config'))
}

for check, status in checks.items():
    print(f'{check}: {'✅ OK' if status else '❌ MISSING'}')
"
```

Expected output:
```
FLASK_SECRET_KEY: ✅ OK
OPENAI_API_KEY: ✅ OK
Database: ✅ OK
OAuth Config: ✅ OK
```

---

## 📋 FILE CHECKLIST

Before starting deployment, verify these files exist:

### **Root Level Files** (6 critical)
```
✅ web_app.py
✅ requirements-voice.txt
✅ .env                         (created from template)
✅ .env.template
✅ .gitignore
✅ README.md
```

### **Source Code** (src/ directory)
```
✅ nlu.py
✅ ai_scheduler.py
✅ agenda_summary.py
✅ ai_patterns.py
✅ email_drafter.py
✅ voice_sentiment.py
✅ task_extractor.py
✅ conversation_manager.py
✅ visual_calendar.py
✅ accessibility.py
✅ auth.py                      (NEW - user authentication)
✅ book.py
✅ get_details.py
```

### **Frontend** (templates/ and static/)
```
✅ templates/login.html
✅ templates/register.html      (NEW - registration form)
✅ templates/dashboard.html
✅ static/style.css
✅ static/app.js
```

### **Configuration** (setup files)
```
✅ .env                         (created from template)
✅ .config/client_secret_*.json (from Google Console)
```

### **Database** (auto-created)
```
✅ app.db                       (created when first accessed)
```

---

## 🧪 VERIFICATION TESTS

Run these to ensure everything is working:

### Test 1: Python Environment
```bash
python --version
# Should be 3.8+
```

### Test 2: Required Packages
```bash
python -c "import flask, google, openai; print('✅ All packages installed')"
```

### Test 3: Database
```bash
python -c "from src.auth import AuthManager; print('✅ Database ready')"
```

### Test 4: Environment Variables
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f\"✅ FLASK_SECRET_KEY: {bool(os.environ.get('FLASK_SECRET_KEY'))}\"); print(f\"✅ OPENAI_API_KEY: {bool(os.environ.get('OPENAI_API_KEY'))}\")"
```

### Test 5: Full Test Suite (Optional but recommended)
```bash
pytest tests/ -v --tb=short
# Should show: 260+ tests passed, 0 failed
```

---

## 🚀 DEPLOYMENT OPTIONS

### Option 1: Local Development (Quick Start)
```bash
# Activate virtual environment
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Run development server
python web_app.py

# Access at: http://localhost:5000
```

### Option 2: Production with Gunicorn
```bash
# Install Gunicorn
pip install gunicorn

# Run production server
gunicorn -w 4 -b 0.0.0.0:8000 web_app:app

# Access at: http://localhost:8000 or your IP:8000
```

### Option 3: Docker (Recommended for Production)
```bash
# Build image
docker build -t calendar-app:1.0 .

# Run container
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-your-key \
  -e FLASK_SECRET_KEY=your-secret \
  calendar-app:1.0

# Access at: http://localhost:8000
```

### Option 4: Systemd Service (Linux)
Create file: `/etc/systemd/system/calendar-app.service`
```ini
[Unit]
Description=Voice Assistant Calendar
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/calendar-app
Environment="PATH=/opt/calendar-app/.venv/bin"
ExecStart=/opt/calendar-app/.venv/bin/gunicorn -w 4 web_app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl start calendar-app
sudo systemctl enable calendar-app
```

---

## ✨ FIRST TIME SETUP SUMMARY

```
1. Create .env from .env.template
2. Fill in FLASK_SECRET_KEY and OPENAI_API_KEY
3. Add Google OAuth credentials to .config/
4. Install dependencies: pip install -r requirements-voice.txt
5. Initialize database: python -c "from src.auth import AuthManager; AuthManager()"
6. Run tests: pytest tests/ -v (optional)
7. Start server: python web_app.py (development)
               OR gunicorn -w 4 -b 0.0.0.0:8000 web_app:app (production)
8. Access at: http://localhost:5000 or http://your-ip:8000
```

---

## 🧠 QUICK REFERENCE

### Environment Variables
| Variable | Purpose | Required | Example |
|----------|---------|----------|---------|
| FLASK_SECRET_KEY | Session security | YES | sk-abc123... |
| OPENAI_API_KEY | ChatGPT access | YES | sk-abc123... |
| ENV | Deployment mode | NO | production |
| OPENAI_MODEL | AI model | NO | gpt-3.5-turbo |
| DATABASE_PATH | SQLite location | NO | app.db |

### Common Deployment Ports
| Service | Port | Usage |
|---------|------|-------|
| Development | 5000 | Local testing |
| Gunicorn | 8000 | Production (behind proxy) |
| Nginx/Apache | 80/443 | Public-facing reverse proxy |

### Key File Locations
| What | Where | Note |
|-----|-------|------|
| Main App | web_app.py | Root directory |
| Configuration | .env | Created from template |
| Credentials | .config/client_secret_*.json | Add manually |
| Database | app.db | Auto-created |
| Templates | templates/ | 3 HTML files |
| Static | static/ | CSS, JavaScript |
| Source | src/ | 13 Python modules |

---

## 🔒 SECURITY REMINDERS

- ✅ Never commit `.env` file to git (already in .gitignore)
- ✅ Never commit `client_secret_*.json` to git (already in .gitignore)
- ✅ Use HTTPS in production (configure Nginx/Apache)
- ✅ Set `ENV=production` in .env for production
- ✅ Generate new FLASK_SECRET_KEY for each deployment
- ✅ Keep OPENAI_API_KEY secret (rotate regularly)
- ✅ Set strong database backup policies
- ✅ Monitor application logs for errors

---

## 🆘 TROUBLESHOOTING

### "ModuleNotFoundError: No module named..."
```bash
# Solution: Install dependencies
pip install -r requirements-voice.txt
```

### "FLASK_SECRET_KEY not set"
```bash
# Solution: Create .env and set the variable
cp .env.template .env
# Edit .env and add FLASK_SECRET_KEY
```

### "OPENAI_API_KEY invalid"
```bash
# Solution: Check your API key
1. Go to https://platform.openai.com/api-keys
2. Generate new key if needed
3. Update OPENAI_API_KEY in .env
4. Test: curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"
```

### "OAuth credentials missing"
```bash
# Solution: Download from Google Cloud Console
1. Visit https://console.cloud.google.com/
2. Go to APIs & Services > Credentials
3. Download OAuth 2.0 Client Secrets (JSON)
4. Place in .config/ directory
5. Verify: ls -la .config/client_secret_*.json
```

### "Port 8000 already in use"
```bash
# Solution: Use different port
gunicorn -b 0.0.0.0:8080 web_app:app
# Or kill the process using port 8000
lsof -i :8000
kill -9 <PID>
```

### "Database locked error"
```bash
# Solution: Remove and reinitialize
rm app.db
python -c "from src.auth import AuthManager; AuthManager()"
```

---

## ✅ READY TO DEPLOY?

Complete this checklist:

```
PRE-DEPLOYMENT CHECKLIST
========================

Setup
  [ ] .env file created and filled
  [ ] Google OAuth credentials added to .config/
  [ ] Dependencies installed (pip install -r requirements-voice.txt)
  [ ] Database initialized (app.db exists)
  [ ] No Python syntax errors

Verification
  [ ] python web_app.py runs without errors
  [ ] 260+ tests passing (pytest tests/ -v)
  [ ] http://localhost:5000 is accessible
  [ ] Registration form works
  [ ] Login page shows

Documentation
  [ ] README.md reviewed
  [ ] QUICK_DEPLOY_GUIDE.md read
  [ ] Environment variables documented

Security
  [ ] .env is in .gitignore
  [ ] client_secret_*.json is in .gitignore
  [ ] FLASK_SECRET_KEY is strong (32+ characters)
  [ ] No API keys in code comments

Ready?
  [ ] YES - Proceed with deployment!
```

---

🚀 **YOU'RE READY TO DEPLOY!**

Choose your deployment option above and follow the steps. If you encounter issues, see the Troubleshooting section.

**Questions?** Check:
- QUICK_DEPLOY_GUIDE.md - Deployment commands
- DEPLOYMENT_CHECKLIST.md - Full deployment verification
- PROJECT_FILE_INVENTORY.md - File organization reference
