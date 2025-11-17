"""Compatibility wrapper for `src.book`.

This module provides thin wrappers that call into `src.book` but keep
the public API available at the top-level `book` module. Wrappers that
perform console output are implemented here so unit tests can patch
`book.print` and `book.get_event_id` as expected.
"""
from typing import Optional
import src.book as _src

# Re-export commonly used helper functions from src.book
def get_event_id(datetime_str: str) -> Optional[str]:
	return _src.get_event_id(datetime_str)

def create_event_user(*args, **kwargs):
	return _src.create_event_user(*args, **kwargs)

def cancel_event_by_start(*args, **kwargs):
	return _src.cancel_event_by_start(*args, **kwargs)

def load_voice_assistant_calendar():
	return _src.load_voice_assistant_calendar()

def cancel_booking(service, username, start_time):
	"""Cancel a booking and print a user-facing message.

	This wrapper calls `get_event_id` from this module so tests can
	patch `book.get_event_id` and intercept behavior.
	"""
	event_id = get_event_id(start_time)
	calendar_id = 'c_3b23a6dcc818ef6fc87099b492db10ff2c4b3d47036a1aede171bc1d19fb0059@group.calendar.google.com'

	if event_id:
		service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
		print('Booking canceled successfully')
	else:
		print('No booking found at the specified time.')

def cancel_booking_command(service, args):
	if hasattr(args, 'username') and hasattr(args, 'start_time'):
		cancel_booking(service, args.username, args.start_time)
	else:
		print("Please provide both username and start time for canceling the booking.")

# Expose rest of src.book namespace for convenience
from src.book import add_30_minutes, search_time, get_attendee  # noqa: F401

__all__ = [
	'get_event_id', 'create_event_user', 'cancel_event_by_start', 'cancel_booking',
	'cancel_booking_command', 'load_voice_assistant_calendar', 'add_30_minutes', 'search_time', 'get_attendee'
]
