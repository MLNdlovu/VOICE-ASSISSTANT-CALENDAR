#!/usr/bin/env bash

# 🤖 AI Voice Assistant Calendar - Quick Start Script
# Run this to get up and running in seconds

echo "=================================================="
echo "🤖 AI Voice Assistant Calendar"
echo "=================================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Install from https://www.python.org"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found"
    exit 1
fi

echo "📦 Installing dependencies..."
pip3 install -r requirements-ai.txt -q

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"
echo ""

# Check .env
if [ ! -f .env ]; then
    echo "⚠️  .env file not found"
    echo "Create .env with:"
    echo ""
    echo "  OPENAI_API_KEY=sk-proj-..."
    echo "  GOOGLE_CLIENT_ID=..."
    echo "  GOOGLE_CLIENT_SECRET=..."
    echo "  DEBUG=True"
    echo ""
    exit 1
fi

echo "✅ .env file found"
echo ""

# Start app
echo "=================================================="
echo "🚀 Starting AI Voice Assistant"
echo "=================================================="
echo ""
echo "📍 Open browser at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop"
echo ""
echo "=================================================="
echo ""

python3 app_ai.py
