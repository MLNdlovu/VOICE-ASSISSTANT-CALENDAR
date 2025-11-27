# Calendar Actions Instructions

This document outlines the functions used for managing calendar events via the voice assistant backend.

## Functions

### create_event

- Purpose: Create a calendar event.
- Input: JSON containing `title`, `date` (YYYY-MM-DD), `time` (HH:MM), and optional details.
- Behavior: Parses date and time server-side, creates event in ISO format in Google Calendar.
- Returns: JSON response indicating success or failure, includes event details.

### get_events

- Purpose: Retrieve events on a specified date.
- Input: JSON containing `date` (YYYY-MM-DD).
- Behavior: Fetches all events for the specified date.
- Returns: JSON array of events with `title`, `iso_time`, `spoken_time`, `duration_minutes`, and `location`.

### cancel_event

- Purpose: Delete/cancel a calendar event.
- Input: JSON containing event identifier.
- Behavior: Deletes the event from the user's calendar.
- Returns: JSON confirmation of deletion or error message.

## Notes

- All responses are JSON structured; no HTML responses are provided.
- Time parsing and formatting to spoken time are handled server-side.
- Event times are stored in ISO 8601 format but returned with human-friendly spoken-time for voice output.
- The backend treats all requests statelessly and single-turn.
