# Voice Router Backend Architecture Instructions

This document describes the backend design principles for the voice assistant's voice routing and processing.

## Stateless Design Principles

- All voice command requests to the backend must be stateless.
- Do NOT store any conversation or chat history on the server.
- Each request should be treated as a single-turn interaction:
  - One transcript in.
  - One action or reply out.
- Do NOT require previously stored chat context or messages.
- Do NOT return old messages or conversation history in any response.
- For follow-up questions or incomplete information detected in the transcript, the backend must respond with:
  - `needs_more_info: true` 
  - Prompting the user to provide the missing information in the next request.

## Trigger Phrase and Security

- The backend stores the trigger phrase securely per user.
- The backend must NOT return the actual trigger phrase to the frontend or any API consumer.
- APIs for trigger phrase management:
  - `/api/set_trigger` - save the trigger phrase securely, returns `{ "ok": true }` without phrase.
  - `/api/get_trigger_status` - returns JSON indicating whether trigger is set, but never returns phrase.
- Trigger detection is performed server-side but fuzzy matching for activation is handled client-side with a stored copy for privacy.

## Voice Command Endpoint

- The main voice command endpoint `/api/voice_cmd` accepts JSON with:
  - `transcript`: raw user text
  - `user_id`: user identifier
  - `context`: ignored (always stateless)
- The endpoint:
  - Normalizes transcript text.
  - Parses transcript into structured JSON with intent details.
  - Invokes appropriate calendar or AI actions.
  - Always returns a minimal response with:
    - `assistant_text`
    - `spoken_time` (natural language)
    - `needs_more_info`
    - `data` (events or other relevant info)
- The endpoint treats each request independently.

## Logging

- Voice commands and detected actions are logged with timestamps and user info in `logs/voice.log`.

## Summary

Ensure all requests and responses comply with stateless, privacy-preserving principles suitable for a secure and scalable voice assistant backend.
