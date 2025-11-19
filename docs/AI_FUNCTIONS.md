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

## AI Assistant Functions

This document describes the AI features available in the Voice Assistant Calendar application and how to use them from the dashboard.

## Overview

The AI Assistant can:

- Generate structured meeting agendas.
- Summarize meeting notes into concise summaries and action items.
- Extract action items from event descriptions or meeting notes.
- Draft emails (subject + body) for invites or follow-ups.
- Suggest possible meeting times based on participants and duration.

All AI features are optional and require a configured AI backend (OpenAI API key) to be available. If AI is not configured, the UI will show an error and the endpoints will return HTTP 503.

## Endpoints

The backend exposes the following endpoints under `/api/ai/`:

- `POST /api/ai/chat` — General chat with the assistant. Body: `{ message: string, context?: string }`.
- `POST /api/ai/agenda` — Generate a meeting agenda. Body: `{ title?: string, duration?: number, participants?: string[], notes?: string }`.
- `POST /api/ai/summarize` — Summarize notes. Body: `{ notes: string }`.
- `POST /api/ai/actions` — Extract action items from notes. Body: `{ title?: string, notes: string }`.
- `POST /api/ai/email` — Draft an email for an event. Body: `{ title: string, recipients?: string[], context?: string }`.
- `POST /api/ai/suggest-times` — Suggest meeting time slots. Body: `{ duration?: number, participants?: string[], preferred_days?: string }`.

All endpoints require the user to be authenticated (login via Google) and return JSON. If AI is not configured, endpoints return a 503 with a helpful message.

## Using AI from the Dashboard

- Open the dashboard and go to the Events tab.
- Each event has AI action buttons:
  - `Agenda` — generate a structured agenda for the event (uses event title as prompt).
  - `Actions` — extract action items from the event description.
  - `Summarize` — paste meeting notes and generate a concise summary.
  - `Draft Email` — draft an email for the event; the assistant will try to include a subject and email body. The UI will attempt to autofill recipients from the event's organizer or attendees when available.
  - `Suggest Times` — request suggested meeting times.

When AI generates content you can optionally save it back to the event description using the Save flow — a confirmation modal lets you choose between `Append` and `Overwrite`.

## Example Client Calls

Overwrite description:

```json
PATCH /api/events/<event_id>/description
{ "description": "New content from AI", "mode": "overwrite" }
```

Append description:

```json
PATCH /api/events/<event_id>/description
{ "description": "Additional AI notes", "mode": "append" }
```

Draft email example request body:

```json
POST /api/ai/email
{ "title": "Project update", "recipients": ["alice@example.com"], "context": "Summary of today's meeting and action items" }
```

## Notes & Troubleshooting

- If `/ai` returns "Not Found", use the "Open Assistant" button on the dashboard. The app also provides a shortlink `/ai` which redirects to the dashboard and opens the modal.
- If you see `AI not configured or not available`, ensure the server can import and initialize the AI client (set `OPENAI_API_KEY` in environment, and install the `openai` Python package if using the hosted integration).

## Security

- Never commit API keys to the repository. Use environment variables or a secure secrets manager.

## Contact

If you want additional AI behaviors (e.g., calendar-aware scheduling that checks attendees' free/busy), I can add integrations to query attendees' availability and provide more accurate time suggestions.
