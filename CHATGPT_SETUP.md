# 🤖 ChatGPT Integration Setup Guide

## Overview

Your Voice Assistant Calendar now includes **AI-powered conversational abilities** using OpenAI's GPT models!

### What You Can Do With ChatGPT:
- 💬 Have natural conversations about scheduling
- 📅 Get smart meeting time suggestions
- 🔍 Get analysis of your calendar
- 💡 Resolve scheduling conflicts
- ❓ Ask calendar management questions
- 🎯 Optimize your schedule

---

## Step 1: Get Your OpenAI API Key

### Option A: Create a Free Account
1. Go to [OpenAI Platform](https://platform.openai.com/signup)
2. Sign up with your email
3. Verify your email
4. Go to [API Keys page](https://platform.openai.com/api-keys)
5. Click "Create new secret key"
6. Copy and save it (shown only once!)

### Option B: Use Existing Account
1. Log in to [OpenAI Platform](https://platform.openai.com)
2. Go to [API Keys](https://platform.openai.com/api-keys)
3. Create a new secret key if you don't have one

### Pricing
- **gpt-3.5-turbo**: ~$0.0015 per 1,000 tokens (~$0.0005 per message)
- **gpt-4**: ~$0.03 per 1,000 tokens (~$0.01 per message)
- Free trial credits: $5-$18 (expires after 3 months)

---

## Step 2: Configure Your API Key

### Method A: Using .env File (Recommended) 🔐

1. **Copy the template:**
```powershell
Copy-Item .env.example .env
```

2. **Edit the .env file:**
   - Open `.env` in VS Code
   - Replace `your-api-key-here` with your actual API key
   - Example:
     ```
     OPENAI_API_KEY=sk-proj-abc123xyz789...
     CHATGPT_MODEL=gpt-3.5-turbo
     ```

3. **Save the file**

⚠️ **Security Note:** Never commit `.env` to Git. It's already in `.gitignore`.

### Method B: Using Environment Variable

**Windows PowerShell:**
```powershell
$env:OPENAI_API_KEY='sk-proj-your-api-key-here'
```

**Windows Command Prompt:**
```cmd
set OPENAI_API_KEY=sk-proj-your-api-key-here
```

**Permanent (Windows):**
1. Press `Win + X` → Choose "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Click "New" under User variables
5. Variable name: `OPENAI_API_KEY`
6. Variable value: Your API key
7. Click OK, restart terminal

---

## Step 3: Test ChatGPT Integration

```powershell
# Navigate to project
cd "C:\Users\Lungelo Ndlovu\Documents\VOICE-ASSISSTANT-CALENDAR"

# Activate venv
.\.venv\Scripts\Activate.ps1

# Test ChatGPT
python ai_chatgpt.py
```

**Expected Output:**
```
✅ ChatGPT chatbot initialized successfully!

Testing basic conversation...

[AI] The best times to schedule meetings typically depend on your industry and team...
```

---

## Step 4: Use ChatGPT in Your Application

### In GUI Mode

Click the new **"🤖 AI Chat"** button to open the ChatGPT interface:

```
┌─────────────────────────────────────────────┐
│   🗓️  Voice Assistant Calendar              │
└─────────────────────────────────────────────┘
│ [📅 Book] [🗑️ Cancel] [📋 View] [🤖 AI Chat]│
└─────────────────────────────────────────────┘
```

### In Python Code

```python
from ai_chatgpt import initialize_chatbot

# Initialize the chatbot
bot = initialize_chatbot()

if bot:
    # Have a conversation
    response = bot.answer_calendar_question(
        "What times are best for study sessions?"
    )
    print(response)
    
    # Get meeting suggestions
    suggestions = bot.suggest_meeting_time(
        "code clinic session", 
        duration_minutes=60
    )
    print(suggestions)
    
    # Analyze your schedule
    analysis = bot.analyze_schedule(your_events_list)
    print(analysis)
else:
    print("ChatGPT not available")
```

---

## Features & Examples

### 1. **Answer Calendar Questions**
```python
bot.answer_calendar_question("How should I structure my daily schedule?")
```

### 2. **Suggest Meeting Times**
```python
suggestions = bot.suggest_meeting_time(
    meeting_type="study group",
    duration_minutes=90
)
```

### 3. **Resolve Conflicts**
```python
help = bot.help_resolve_conflict(
    "I have two meetings at the same time on Friday"
)
```

### 4. **Analyze Your Schedule**
```python
analysis = bot.analyze_schedule(events_list)
# Gets insights like: "You're overbooked", "Good break times", etc.
```

### 5. **Free-form Chat**
```python
response = bot.chat("What's the best way to organize my calendar?")
```

---

## Configuration Options

### Choose Your Model

Edit `.env` or in code:

```python
# Fast and cheap (default)
bot = initialize_chatbot(model="gpt-3.5-turbo")

# Smart and detailed (more expensive)
bot = initialize_chatbot(model="gpt-4")
```

### Adjust Conversation History

```python
bot = CalendarChatbot()
bot.max_history = 20  # Keep more context
```

### Clear Conversation History

```python
bot.clear_history()  # Start fresh conversation
```

---

## Troubleshooting

### Error: "API key not found"

**Solution:**
```powershell
# Check if .env exists
Test-Path .env

# Check if API key is set
$env:OPENAI_API_KEY

# If empty, set it
$env:OPENAI_API_KEY='your-api-key'
```

### Error: "openai not installed"

**Solution:**
```powershell
.\.venv\Scripts\Activate.ps1
pip install openai python-dotenv
```

### Error: "Invalid API key"

**Solution:**
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Make sure key starts with `sk-proj-`
3. Check if key is active (not revoked)
4. Copy entire key (don't miss any characters)

### Slow Responses

**Causes & Solutions:**
- Network latency (normal, 1-3 seconds)
- Model busy (use gpt-3.5-turbo instead of gpt-4)
- Rate limited (wait a minute, then retry)

### No Response or Blank Response

**Solution:**
```python
try:
    response = bot.chat("Hello")
    if response:
        print(response)
    else:
        print("Empty response - check API connection")
except Exception as e:
    print(f"Error: {e}")
```

---

## Cost Estimation

### Usage Scenarios

**Light Use** (10 conversations/day):
- 300 conversations/month
- Cost: ~$0.15/month (gpt-3.5-turbo)

**Medium Use** (50 conversations/day):
- 1,500 conversations/month
- Cost: ~$0.75/month (gpt-3.5-turbo)

**Heavy Use** (200+ conversations/day):
- 6,000+ conversations/month
- Cost: ~$3/month (gpt-3.5-turbo)
- Recommendation: Use gpt-3.5-turbo

**All with gpt-4 (multiply costs by ~20)**

---

## Security Best Practices

### ✅ Do's
- ✅ Store API key in `.env` file
- ✅ Add `.env` to `.gitignore` (already done)
- ✅ Never share your API key
- ✅ Rotate keys periodically
- ✅ Use separate API keys for dev/prod

### ❌ Don'ts
- ❌ Commit `.env` to Git
- ❌ Share API key in code
- ❌ Post key in public forums
- ❌ Hardcode key in application
- ❌ Use same key across projects

---

## Advanced Usage

### Add Custom System Prompt

```python
from ai_chatgpt import CalendarChatbot

bot = CalendarChatbot()

# Override the system prompt
custom_prompt = """You are a friendly calendar assistant...
Your specific responsibilities are..."""

bot._build_system_prompt = lambda: custom_prompt
```

### Track Token Usage

```python
# After each chat
info = bot.get_model_info()
print(f"Conversation history: {info['conversation_history_length']} messages")
```

### Batch Processing

```python
questions = [
    "What are peak productivity hours?",
    "How long should meetings be?",
    "Best day for planning?"
]

for q in questions:
    response = bot.chat(q)
    print(f"Q: {q}\nA: {response}\n")
```

---

## Integration with Calendar

### Get Smart Suggestions

```python
from ai_chatgpt import initialize_chatbot
import book
import get_details

bot = initialize_chatbot()

if bot:
    # Get AI suggestion for best time
    suggestion = bot.suggest_meeting_time("code clinic", 60)
    print(suggestion)
    
    # Then book it
    email = get_details.get_email()
    date = get_details.get_date()  # Now supports natural language!
    time = get_details.get_time()
    
    book.book_as_student(service, email, f"{date}T{time}", "Code Clinic")
```

---

## Disable ChatGPT (If Needed)

Simply don't set the `OPENAI_API_KEY` environment variable. The application will fall back to the regular calendar interface.

---

## Support & Resources

- **OpenAI Docs:** https://platform.openai.com/docs
- **API Reference:** https://platform.openai.com/docs/api-reference
- **Pricing:** https://openai.com/pricing
- **Community:** https://community.openai.com

---

## What's Next?

### Possible Enhancements:
1. **Calendar-aware responses** - ChatGPT sees your actual events
2. **Automated scheduling** - ChatGPT suggests AND books events
3. **Multi-language support** - Chat in any language
4. **Custom instructions** - Personalized AI responses
5. **Integration with other models** - Claude, Gemini alternatives

---

## Summary

| Feature | Status | Cost |
|---------|--------|------|
| ChatGPT Integration | ✅ Complete | API usage |
| .env Configuration | ✅ Ready | Free |
| GUI Chat Interface | ✅ Available | Free |
| API Key Setup | ✅ Easy | ~$0-15/month |
| All Features | ✅ Working | Varies |

---

**Enjoy your AI-powered calendar! 🤖📅**

*Last Updated: November 13, 2025*
