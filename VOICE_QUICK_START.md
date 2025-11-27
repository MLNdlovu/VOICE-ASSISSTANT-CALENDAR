# Voice Assistant Quick Start Guide

## 🎤 Getting Started with Voice Commands

### First Time Setup

1. **Register Your Account**
   - Visit http://localhost:5000
   - Click "Create Account"
   - Enter: First Name, Last Name, Email
   - Set Your Voice Trigger (2 letters + 2 numbers, e.g., `EL25`)
   - Click "Create Account & Continue"

2. **Authenticate with Google**
   - Click "Sign in with Google"
   - Authorize calendar access
   - You'll be directed to profile completion

3. **Voice Greeting**
   - After login, hear: "Hello, what can I do for you today?"
   - Voice assistant is now active!

### Voice Trigger Activation

When you see the voice indicator (glowing circle), the assistant is listening:

1. **Say Your Trigger Word**
   - Example: "Ellen Twenty-Five" or "E-L Two Five"
   - The system understands variations

2. **System Acknowledges**
   - You'll hear: "Yes, what can I do for you?"
   - Now speak your command

### Voice Commands

#### 📅 Book a Meeting
```
"Book a meeting with John tomorrow at 2pm"
"Schedule team standup Monday at 9am"
"Create event called project review Friday at 3pm"
"Add meeting about Q4 planning next Tuesday at 10:30am"
```
→ System books event and shows confirmation

#### 📋 List Events
```
"What's on my calendar today?"
"Show events for tomorrow"
"Any meetings this week?"
"What events do I have?"
"My schedule for Friday"
```
→ System reads your upcoming events

#### ⏰ Set Reminders
```
"Remind me to call mom at 5pm"
"Set a reminder for the dentist appointment tomorrow at 2pm"
"Create reminder for project deadline Friday"
```
→ System creates notification reminder

#### 💬 Ask Questions
```
"What time is my next meeting?"
"How many meetings today?"
"Do I have time for lunch?"
"Am I free tomorrow afternoon?"
```
→ System provides calendar insights

#### 😊 Casual Conversation
```
"Hello!"
"How are you today?"
"Thanks!"
"Good morning"
```
→ Friendly responses while staying focused on calendar

## 🎨 Understanding the UI

### Voice Indicator States

**🔵 Listening (Blue Pulse)**
- System is capturing your voice
- Speak clearly and naturally
- 3 expanding rings = active listening

**🟢 Speaking (Green Pulse)**
- Assistant is providing response
- You'll hear audio feedback
- Wait for completion before speaking

**⚫ Ready/Idle (Gray)**
- System is standby mode
- Waiting for trigger word
- No listening active

### Chat History
- Shows your commands (blue)
- Shows assistant responses (green)
- Scrolls automatically as conversation grows
- Timestamp for each message

### Voice Animations
- **Waveform bars**: Rise and fall with voice detection
- **Glowing circle**: Pulses faster with speaker intensity
- **Status indicator**: Shows current mode

## 🎯 Tips for Best Results

### Speak Clearly
- Use natural, conversational tone
- Avoid mumbling
- Normal speaking volume
- Clear pronunciation of names/numbers

### Quiet Environment
- Minimize background noise
- Close windows if outside noise
- Mute other audio
- Move away from fans/AC

### Natural Phrasing
Good:
- "Book a meeting with Sarah tomorrow at 2pm"
- "Show me today's schedule"

Avoid:
- "BOOK A MEETING" (too loud/formal)
- Technical jargon when unnecessary

### Complete Information
Provide all details upfront:
- ✅ "Book meeting with John tomorrow at 2pm"
- ❌ "Book a meeting" (system will ask for details)

## ⚠️ Troubleshooting

### "I didn't catch that"
- Speak more clearly
- Reduce background noise
- Try again with rephrasing

### Trigger not recognized
- Say trigger naturally: "Ellen Twenty-Five"
- Don't spell it out letter-by-letter
- Say it with confidence

### Browser says "Microphone not available"
- Check Windows settings for microphone access
- Grant permission to browser
- Try different browser (Chrome/Edge recommended)

### Calendar conflict warning
- System detects overlapping meeting
- Choose to:
  - "Use different time" (hear alternatives)
  - "Cancel request"
  - "Overwrite old meeting" (confirm change)

## 📊 Checking Your Usage

Click **Voice Stats** (if available) to see:
- Total voice commands used
- Success rate (%)
- Most common commands
- Average response time
- Command history

## 🔧 Advanced Features

### Manual Typing Fallback
If voice not working:
1. Look for chat input box
2. Type your command manually
3. Press Enter to submit
4. System processes text commands too

### View Transcript
Session transcript shows:
- All your commands (what system heard)
- All responses (what assistant said)
- Intent detected
- Parameters extracted
- Success/failure status

## 🚀 Voice Command Examples

**Monday Planning:**
- "What's scheduled for this week?"
- "Book team meeting Wednesday at 10am"
- "Set reminder for Friday deadline at 5pm"
- "Any free slots tomorrow afternoon?"

**Day Management:**
- "What time is my next meeting?"
- "Show today's events"
- "How much free time do I have?"
- "Book lunch block 12-1pm"

**Meeting Scheduling:**
- "Schedule sync with engineering Friday at 2pm"
- "Book 1-on-1 with my manager next Tuesday"
- "Create recurring standup Monday-Friday at 9am"
- "Add call with client next week"

**Reminders:**
- "Remind me birthday is next week"
- "Set reminder for car maintenance"
- "Alert me before meeting"

## 🔐 Privacy & Security

✅ **What's Saved:**
- Your commands (text only, not audio)
- System responses
- Command type and intent
- Parameters extracted
- Success/failure status
- Timestamps

❌ **What's NOT Saved:**
- Raw audio recordings
- Voice recordings
- Passwords or sensitive data
- Browser cookies

🔒 **Protection:**
- Session-based (logs out automatically)
- User data isolated per account
- No sharing with third parties
- SSL/HTTPS in production

## 📞 Support

If voice features aren't working:

1. **Check Browser Support**
   - Chrome/Edge: ✅ Full support
   - Firefox: ⚠️ Limited support
   - Safari: ❌ No support

2. **Verify Permissions**
   - Browser needs microphone access
   - Operating system needs microphone enabled
   - Check volume not muted

3. **Test Microphone**
   - Use system voice recorder
   - Verify microphone works
   - Test in quiet environment

4. **Clear Cache**
   - Clear browser cache/cookies
   - Refresh page (Ctrl+F5)
   - Try again

5. **Alternative Method**
   - Use manual text input instead
   - All features available via typing

## 🎓 Learning Resources

- **Web Speech API**: https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API
- **Voice Recognition Tips**: https://www.nngroup.com/articles/voice-recognition/
- **Natural Language Processing**: Introduction in system docs

## 🎉 You're Ready!

Your voice assistant is configured and ready to use. Just:
1. Say your trigger word
2. Speak your command naturally
3. Hear confirmation from assistant
4. Calendar updates automatically

Enjoy hands-free calendar management! 🎤📅

---

**Tip:** The more you use voice commands, the better the system learns your preferences and communication style.

**Keyboard Shortcuts (Future):**
- `Ctrl+Shift+V` - Start voice input
- `Ctrl+,` - Settings (coming soon)
- `Ctrl+H` - View history (coming soon)
