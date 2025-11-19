# AI Functions and Integration

This document lists the AI-related functions and modules used in the Voice Assistant Calendar project and suggests additional AI features that could be added.

---

## Existing AI modules

### `src/ai_chatgpt.py` (CalendarChatbot)
This module integrates with the OpenAI API and provides the following features:

- `CalendarChatbot.__init__(api_key: Optional[str], model: str)`
  - Initializes the ChatGPT client and sets up conversation history.
  - Requires `OPENAI_API_KEY` environment variable or `api_key` parameter.

- `CalendarChatbot._build_system_prompt()`
  - Internal: builds the system prompt that instructs the model how to behave as a calendar assistant.

- `CalendarChatbot.chat(user_message: str, calendar_context: Optional[Dict]) -> str`
  - Sends a user message (optionally with calendar context) to the API and returns the AI response.
  - Manages short-term conversation history for context-aware replies.

- `CalendarChatbot.suggest_meeting_time(meeting_type: str, duration_minutes: int = 30) -> str`
  - Asks the model to suggest optimal meeting times for a given meeting type and duration.

- `CalendarChatbot.answer_calendar_question(question: str) -> str`
  - General Q&A about calendar management.

- `CalendarChatbot.help_resolve_conflict(conflict_description: str) -> str`
  - Uses the AI to propose ways of resolving scheduling conflicts.

- `CalendarChatbot.analyze_schedule(events_list: List[Dict]) -> str`
  - Provides analysis of a user's schedule (e.g., overbooked, breaks, suggestions).

- `CalendarChatbot._format_calendar_context(context: Dict) -> str`
  - Formats calendar information for inclusion in prompts to the model.

- `CalendarChatbot.clear_history()`
  - Clears the local conversation history buffer.

- `CalendarChatbot.get_model_info() -> Dict`
  - Returns information about current model and history state.

- `is_chatgpt_available()`
  - Helper to check whether the `openai` client is available and API key set.

- `initialize_chatbot(api_key: Optional[str], model: str)`
  - Safe initialization helper that returns a `CalendarChatbot` instance or `None`.


## AI-adjacent modules

- `src/voice_handler.py`
  - Uses regex-based parsing and `dateutil` to interpret natural-language booking requests.
  - Uses `pyttsx3` for TTS (if available) and `speech_recognition` for speech-to-text.
  - Although not calling a large language model, it provides NLP-style parsing and could be combined with the ChatGPT module for enhanced NLU.


## Environment & Installation Notes

- The ChatGPT integration depends on the `openai` Python client (or `openai` library-compatible client). Install with:

```powershell
pip install openai
```

- The ChatGPT client expects `OPENAI_API_KEY` to be set as an environment variable. You can also provide the key when initializing `CalendarChatbot`.

- Voice input requires `SpeechRecognition` and a microphone driver. Text-to-speech uses `pyttsx3`.


## Suggested AI features to add

Below are concrete AI enhancements that would add value to the product. These are grouped by effort/impact.

High-impact ideas:
- Auto-summarize meeting notes: After an event ends, allow the user to paste notes and generate a short meeting summary to attach to the event or email to participants.
- Agenda generation: Given an event title and participants, auto-generate a meeting agenda and suggested time allocations for items.
- Smart rescheduling assistant: Provide recommendations to move events based on priority, suggested buffers, and participant availability.
- Email / message drafting: Draft polite follow-ups, invites, or cancellations using event context.
- Conflict resolver: Automatically propose resolutions for double-bookings, with suggested times and rationale.

Medium-impact ideas:
- Event title normalization: Use the LLM to clean and normalize user-provided event titles (e.g., convert "proj talk" → "Project Discussion: API v2").
- Auto-tagging: Suggest tags or categories for events ("study", "meeting", "personal") for filtering and analytics.
- Smart reminders: Recommend reminder timings based on event type and user habits (e.g., 1 hour before for meetings, 24 hours for deadlines).
- Meeting length prediction: Predict appropriate meeting length from the description.

Low-effort / exploratory ideas:
- Sentiment / urgency detection: Flag events or messages that sound urgent or emotional.
- Natural language calendar queries: Expand the NLU so users can ask multi-step questions like "Move my 3pm meeting to the next available 30 minute slot tomorrow morning".
- Multi-language support: Auto-detect language and use the LLM to parse commands in other languages.
- Voice-based intent clarification: If the intent is ambiguous, ask a short clarifying question before booking.


## Example prompts and usage patterns

- Suggest meeting time:
```
I need a 45 minute study session for my algorithms course. When should I schedule it this week?
```

- Resolve conflict:
```
I have two overlapping meetings tomorrow at 3 PM and 3:30 PM with different participants. How can I resolve this?
```

- Generate agenda:
```
Create a meeting agenda for a 60-minute planning session about the new website redesign -- include time allocations.
```


## Privacy and safety notes

- Do not log or send sensitive personal data (passwords, private IDs) to third-party AI APIs.
- Ensure that users consent to any third-party API usage and are aware of where their data is sent.


## Next steps to integrate suggested features

- Add endpoints in `web_app.py` to call `CalendarChatbot` for agenda generation, summarization, and conflict resolution.
- Create UI flows (modals) to show AI suggestions and allow the user to accept, edit, or discard them.
- Add telemetry / usage flags to opt users into AI features and save preferences.


---

If you'd like, I can implement one of the suggested features now (pick one), add an "AI Assistant" modal to the UI, and wire a backend endpoint to `CalendarChatbot` to test it end-to-end.
