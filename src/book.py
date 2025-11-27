# Student Book a slot
import datetime
import json
from prettytable import PrettyTable
from googleapiclient.errors import HttpError
import os

# Note: book_as_student has been removed. Use create_event_user instead for generic calendar events.

def add_30_minutes(time_str):
    """
    Adds 30 minutes to a given time string.

    Parameters:
    - time_str: A string representing a time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS).

    Returns:
    A string representing the time after adding 30 minutes in ISO 8601 format.

    Raises:
    None

    This function takes a time string in ISO 8601 format and adds 30 minutes to it.
    It returns the resulting time as a string in the same format.

    Example:
    ```
    import datetime

    # Time string in ISO 8601 format
    time_str = '2024-03-01T10:00:00'

    # Add 30 minutes to the time string
    new_time_str = add_30_minutes(time_str)
    print(new_time_str)  # Output: '2024-03-01T10:30:00'
    ```
    """

    time_obj = datetime.datetime.fromisoformat(time_str)
    new_time_obj = time_obj + datetime.timedelta(minutes=30)
    new_time_str = new_time_obj.isoformat()
    
    return new_time_str

def load_voice_assistant_calendar():
    """
    Loads voice assistant calendar events from a JSON file.

    Returns:
    A list of calendar events loaded from the JSON file. If the file is not found or
    if there is an error decoding JSON, an empty list is returned.

    Raises:
    None

    This function attempts to load voice assistant calendar events from a JSON file named
    'voice_assistant_calendar.json'. If the file exists and can be successfully read,
    it loads the events as a list. If there is any error in decoding JSON or if the
    file is not found, it returns an empty list.

    Example:
    ```
    # Load voice assistant calendar events
    events = load_voice_assistant_calendar()
    print(events)
    ```
    """
    try:
        with open("voice_assistant_calendar.json", "r") as file:
            events = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        events = []
    return events

def search_time(search_dateTime):
    """
    Searches for events matching a specific date and time.

    Parameters:
    - search_dateTime: The date and time string to search for in ISO 8601 format (YYYY-MM-DDTHH:MM:SS).

    Returns:
    A list of events that match the provided date and time. If no matching events are found, an empty list is returned.

    Raises:
    None

    This function searches for events in the calendar that match the provided date and time string.
    It iterates through the list of loaded calendar events and checks if the start date and time of each event match
    the provided search_dateTime. Matching events are appended to a list and returned.

    Example:
    ```
    # Search for events matching a specific date and time
    search_dateTime = '2024-03-01T10:00:00'
    matching_events = search_time(search_dateTime)
    print(matching_events)
    ```

    """

    matching_events = []

    for event in load_voice_assistant_calendar():
        if 'start' in event and 'dateTime' in event['start'] and event['start']['dateTime'] == search_dateTime:
            matching_events.append(event)

    return matching_events

def get_event_id(datetime):
    """
    Retrieves the event ID associated with a specified date and time.

    Parameters:
    - datetime: The date and time string to search for in ISO 8601 format (YYYY-MM-DDTHH:MM:SS).

    Returns:
    The event ID associated with the specified date and time, if found. Otherwise, returns None.

    Raises:
    None

    This function retrieves the event ID associated with the specified date and time from the calendar.
    It iterates through the list of loaded calendar events and checks if the start date and time of each event
    match the provided datetime string. If a matching event is found, its ID is returned. If no matching event is
    found, None is returned.

    Example:
    ```
    # Retrieve the event ID for a specified date and time
    event_datetime = '2024-03-01T10:00:00'
    event_id = get_event_id(event_datetime)
    print(event_id)
    ```

    """

    for event in load_voice_assistant_calendar():
        if 'start' in event and 'dateTime' in event['start'] and event['start']['dateTime'] == datetime:
            return event['id']

def get_attendee(datetime):
    """
    Retrieves the attendees of an event associated with a specified date and time.

    Parameters:
    - datetime: The date and time string to search for in ISO 8601 format (YYYY-MM-DDTHH:MM:SS).

    Returns:
    A list of attendees for the event associated with the specified date and time. If no matching event is found,
    returns an empty list.

    Raises:
    None

    This function retrieves the attendees of an event associated with the specified date and time from the calendar.
    It iterates through the list of loaded calendar events and checks if the start date and time of each event
    match the provided datetime string. If a matching event is found, it returns the list of attendees for that event.
    If no matching event is found, an empty list is returned.

    Example:
    ```
    # Retrieve the attendees for a specified date and time
    event_datetime = '2024-03-01T10:00:00'
    attendees = get_attendee(event_datetime)
    print(attendees)
    ```

    """

    for event in load_voice_assistant_calendar():
        if 'start' in event and 'dateTime' in event['start'] and event['start']['dateTime'] == datetime:
            return event['attendees']
        
        
# TODO: Cancel booking. Students cancel booking made by them.


def cancel_booking(service, username, start_time):
    """
    Cancels a calendar event booking.

    Parameters:
    - service: An authenticated Google Calendar service object.
    - username: The username of the user canceling the booking.
    - start_time: The start time of the event in RFC3339 format.

    Returns:
    None

    Raises:
    None

    This function cancels a calendar event booking.
    It retrieves the event ID associated with the specified start time.
    If an event is found, it deletes the event from the Google Calendar.
    If no event is found, it prints a message indicating that no booking was found.

    Example:
    ```
    from googleapiclient.discovery import build

    # Build Google Calendar service
    service = build('calendar', 'v3', credentials=credentials)

    # Cancel a booking
    username = 'example_user'
    start_time = '2024-03-01T10:00:00Z'
    cancel_booking(service, username, start_time)
    ```
    """
    event_id = get_event_id(start_time)
    calendar_id = 'c_3b23a6dcc818ef6fc87099b492db10ff2c4b3d47036a1aede171bc1d19fb0059@group.calendar.google.com'
    
    if event_id:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        print('Booking canceled successfully')
    else:
        print('No booking found at the specified time.')

def cancel_booking_command(service, args):
    """
    Cancels a calendar event booking based on command-line arguments.

    Parameters:
    - service: An authenticated Google Calendar service object.
    - args: Command-line arguments containing username and start time.

    Returns:
    None

    Raises:
    None

    This function cancels a calendar event booking based on the provided command-line arguments.
    It checks if the provided arguments contain both username and start time.
    If both username and start time are provided, it calls the cancel_booking function to cancel the booking.
    If any of the required arguments are missing, it prints a message asking to provide both username and start time.

    Example:
    ```
    from googleapiclient.discovery import build
    import argparse

    # Build Google Calendar service
    service = build('calendar', 'v3', credentials=credentials)

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Cancel booking for a calendar event.')
    parser.add_argument('--username', type=str, help='Username of the user who booked the event')
    parser.add_argument('--start_time', type=str, help='Start time of the event in RFC3339 format')
    args = parser.parse_args()

    # Cancel booking based on command-line arguments
    cancel_booking_command(service, args)
    ```
    """

    if hasattr(args, 'username') and hasattr(args, 'start_time'):
        cancel_booking(service, args.username, args.start_time)
    else:
        print("Please provide both username and start time for canceling the booking.")
# Volunteer helpers removed to simplify API surface


def create_event_user(service, calendar_id='primary', email=None, start_time_iso=None, summary='Event', duration_minutes=30, reminders: list = [10]):
    """
    Create a calendar event in the specified calendar (default: primary).

    Parameters:
    - service: Google Calendar service
    - calendar_id: Calendar ID (default 'primary')
    - email: Optional attendee email
    - start_time_iso: RFC3339 start time string (e.g., '2026-03-23T10:00:00+02:00')
    - summary: Event title
    - duration_minutes: Event duration in minutes
    - reminders: List of reminder minutes (e.g., [10, 30])

    Returns: created event resource or None on failure
    """
    try:
        if not start_time_iso:
            print("create_event_user: start_time_iso is required")
            return None

        # Parse start time
        try:
            start_dt = datetime.datetime.fromisoformat(start_time_iso)
        except Exception:
            # Try to parse without timezone then append +02:00
            try:
                start_dt = datetime.datetime.fromisoformat(start_time_iso + "+02:00")
            except Exception as e:
                print(f"Invalid start_time_iso: {e}")
                return None

        end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)

        event_body = {
            'summary': summary,
            'start': {'dateTime': start_dt.isoformat()},
            'end': {'dateTime': end_dt.isoformat()},
            'reminders': {
                'useDefault': False,
                'overrides': [{'method': 'popup', 'minutes': m} for m in reminders]
            }
        }

        if email:
            event_body['attendees'] = [{'email': email}]

        created = service.events().insert(calendarId=calendar_id, body=event_body).execute()
        print(f"Event created: {created.get('id')}")
        return created
    except Exception as e:
        print(f"Failed to create event: {e}")
        return None


def cancel_event_by_start(service, calendar_id='primary', start_time_iso=None, summary=None):
    """
    Cancel (delete) an event in the specified calendar by its start time.

    Parameters:
    - service: Google Calendar service
    - calendar_id: Calendar ID
    - start_time_iso: RFC3339 start time
    - summary: Optional summary to match

    Returns: True if deleted, False otherwise
    """
    if not start_time_iso:
        print("cancel_event_by_start: start_time_iso required")
        return False

    try:
        # Use a small window to find the event
        try:
            start_dt = datetime.datetime.fromisoformat(start_time_iso)
        except Exception:
            start_dt = datetime.datetime.fromisoformat(start_time_iso + "+02:00")

        time_min = (start_dt - datetime.timedelta(minutes=1)).isoformat()
        time_max = (start_dt + datetime.timedelta(minutes=1)).isoformat()

        events_result = service.events().list(calendarId=calendar_id, timeMin=time_min, timeMax=time_max, singleEvents=True).execute()
        events = events_result.get('items', [])

        for e in events:
            if summary and summary.lower() not in e.get('summary', '').lower():
                continue
            service.events().delete(calendarId=calendar_id, eventId=e['id']).execute()
            print('Event cancelled successfully')
            return True

        print('No matching event found to cancel')
        return False
    except Exception as e:
        print(f"Error cancelling event: {e}")
        return False

if os.environ.get('FLASK_ENV') == 'development' or os.environ.get('DEV_ALLOW_INSECURE') == '1':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
