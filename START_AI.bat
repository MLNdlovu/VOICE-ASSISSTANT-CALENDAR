@echo off
REM 🤖 AI Voice Assistant Calendar - Quick Start (Windows)
REM Run this to get up and running in seconds

echo.
echo ==================================================
echo 🤖 AI Voice Assistant Calendar
echo ==================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Install from https://www.python.org
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Python found: %PYTHON_VERSION%
echo.

REM Check .env
if not exist .env (
    echo ⚠️  .env file not found
    echo.
    echo Create .env with:
    echo.
    echo   OPENAI_API_KEY=sk-proj-...
    echo   GOOGLE_CLIENT_ID=...
    echo   GOOGLE_CLIENT_SECRET=...
    echo   DEBUG=True
    echo.
    pause
    exit /b 1
)

echo ✅ .env file found
echo.

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements-ai.txt -q

if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed
echo.

REM Start app
echo ==================================================
echo 🚀 Starting AI Voice Assistant
echo ==================================================
echo.
echo 📍 Open browser at: http://localhost:5000
echo.
echo Press Ctrl+C to stop
echo.
echo ==================================================
echo.

python app_ai.py

pause
