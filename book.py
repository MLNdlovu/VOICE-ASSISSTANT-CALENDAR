# Student Book a slot
import datetime
import json
from prettytable import PrettyTable
import view

# TODO: Book as a volunteer, a student with more knowledge and/or 
# free period to volunteer for a code clinics session
def book_as_volunteer(service,username,start_time):
    """
    Books a volunteer slot for a code clinic session.

    Parameters:
    - service: An authenticated Google Calendar service object.
    - username: The username of the volunteer.
    - start_time: The start time of the code clinic session in RFC3339 format.

    Returns:
    None

    Raises:
    None

    This function checks if the slot for the given start time is available.
    If available, it books the slot by adding an event to the Google Calendar.
    If not available, it prints a message indicating that the slot is already booked.

    Note:
    - This function relies on other helper functions: search_time, view.view_student_event,
    view.view_code_clinics, and add_30_minutes.
    - The calendar ID used for booking the event is 'c_3b23a6dcc818ef6fc87099b492db10ff2c4b3d47036a1aede171bc1d19fb0059@group.calendar.google.com'.
    - The event summary is set as 'Code Clinic Session'.
    - The end time of the event is calculated by adding 30 minutes to the start time.
    - The attendee's email is generated using the provided username.

    Example:
    ```
    from googleapiclient.discovery import build
    from datetime import datetime

    # Build Google Calendar service
    service = build('calendar', 'v3', credentials=credentials)

    # Book a slot as a volunteer
    username = 'example_user'
    start_time = '2024-03-01T10:00:00Z'
    book_as_volunteer(service, username, start_time)
    ```
    """
    
    # Generate email based on username format
    if "@" in username:
        attendee_email = username
    else:
        attendee_email = username + '@student.wethinkcode.co.za'
    
    if len(search_time(start_time)) < 2:

        view.view_student_event(service,username)
        view.view_code_clinics(service)
        calendar_id='c_3b23a6dcc818ef6fc87099b492db10ff2c4b3d47036a1aede171bc1d19fb0059@group.calendar.google.com'
        event = {
            'summary': 'Code Clinic Session',
            
            'start': {'dateTime': start_time},
            'end': {'dateTime': add_30_minutes(start_time)},
            'attendees': [
                    {'email':  attendee_email }
                    ]
        }
        
        response = service.events().insert(calendarId=calendar_id, body=event).execute()
        print('slot was booked sucessfully')
    else:
        print('slot already booked')
        
        
# TODO: Book as a student, students are able to book a slot of a free volunteer.
def book_as_student(service,username,start_time,summary):
    """
    Books a slot for a code clinic session as a student.

    Parameters:
    - service: An authenticated Google Calendar service object.
    - username: The username of the student booking the slot.
    - start_time: The start time of the code clinic session in RFC3339 format.
    - summary: Summary of the event to be booked.

    Returns:
    None

    Raises:
    None

    This function books a slot for a code clinic session as a student if the slot is available.
    It checks if the slot is free by verifying the number of attendees for the given start time.
    If the slot is available, the student can book it by adding an event to the Google Calendar.
    The event includes the student and a volunteer as attendees.

    Note:
    - The function relies on helper functions: get_attendee, search_time, and get_event_id.
    - The calendar ID for code clinics is 'c_3b23a6dcc818ef6fc87099b492db10ff2c4b3d47036a1aede171bc1d19fb0059@group.calendar.google.com'.
    - If the slot is available, the function patches the existing event with the student and volunteer as attendees.
    - The summary provided is used for the event description.

    Example:
    ```
    from googleapiclient.discovery import build
    from datetime import datetime

    # Build Google Calendar service
    service = build('calendar', 'v3', credentials=credentials)

    # Book a slot as a student
    username = 'example_user'
    start_time = '2024-03-01T10:00:00Z'
    summary = 'Code Clinic Session'
    book_as_student(service, username, start_time, summary)
    ```
    """
    code_clinics_id='c_3b23a6dcc818ef6fc87099b492db10ff2c4b3d47036a1aede171bc1d19fb0059@group.calendar.google.com'
    
    # Generate email based on username format
    if "@" in username:
        attendee_email = username
    else:
        attendee_email = username + '@student.wethinkcode.co.za'
    
    try:
        if len(get_attendee(start_time))==1:

            if len(search_time(start_time))<2:
                volunteer=get_attendee(start_time)[0]['email']
            
                event_id=get_event_id(start_time)
                request_body = {
                            'summary':summary,
                            'attendees': [
                            {'email':  username+"@student.wethinkcode.co.za"},
                            {'email': volunteer}
                            ]
                        }
                service.events().patch(calendarId=code_clinics_id, eventId=event_id, body=request_body).execute()
    except TypeError as t:
        print("the slot is not available")
        print("try booking a slot that has been volunteered for")

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

def load_code_clinics_calender():
    """
    Loads code clinics calendar events from a JSON file.

    Returns:
    A list of calendar events loaded from the JSON file. If the file is not found or
    if there is an error decoding JSON, an empty list is returned.

    Raises:
    None

    This function attempts to load code clinics calendar events from a JSON file named
    'code_clinics_calendar.json'. If the file exists and can be successfully read,
    it loads the events as a list. If there is any error in decoding JSON or if the
    file is not found, it returns an empty list.

    Example:
    ```
    # Load code clinics calendar events
    events = load_code_clinics_calendar()
    print(events)
    ```
    """
    try:
        with open("code_clinics_calendar.json", "r") as file:
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

    This function searches for events in the code clinics calendar that match the provided date and time string.
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

    for event in load_code_clinics_calender():
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

    This function retrieves the event ID associated with the specified date and time from the code clinics calendar.
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

    for event in load_code_clinics_calender():
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

    This function retrieves the attendees of an event associated with the specified date and time from the code clinics
    calendar. It iterates through the list of loaded calendar events and checks if the start date and time of each event
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

    for event in load_code_clinics_calender():
        if 'start' in event and 'dateTime' in event['start'] and event['start']['dateTime'] == datetime:
            return event['attendees']
        
        
# TODO: Cancel booking. Students cancel booking made by them.


def cancel_booking(service, username, start_time):
    """
    Cancels a booking for a code clinic session.

    Parameters:
    - service: An authenticated Google Calendar service object.
    - username: The username of the user attempting to cancel the booking.
    - start_time: The start time of the code clinic session in RFC3339 format.

    Returns:
    None

    Raises:
    None

    This function cancels a booking for a code clinic session.
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
    Cancels a booking for a code clinic session based on command-line arguments.

    Parameters:
    - service: An authenticated Google Calendar service object.
    - args: Command-line arguments containing username and start time.

    Returns:
    None

    Raises:
    None

    This function cancels a booking for a code clinic session based on the provided command-line arguments.
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
    parser = argparse.ArgumentParser(description='Cancel booking for a code clinic session.')
    parser.add_argument('--username', type=str, help='Username of the user who booked the session')
    parser.add_argument('--start_time', type=str, help='Start time of the session in RFC3339 format')
    args = parser.parse_args()

    # Cancel booking based on command-line arguments
    cancel_booking_command(service, args)
    ```
    """

    if hasattr(args, 'username') and hasattr(args, 'start_time'):
        cancel_booking(service, args.username, args.start_time)
    else:
        print("Please provide both username and start time for canceling the booking.")


# TODO: Cancel volunter slot booking. Students cancel booking made by them.


def is_volunteer(username, start_time):
    """
    Checks if a user is booked as a volunteer for a code clinic session at a specified start time.

    Parameters:
    - username: The username of the user to check.
    - start_time: The start time of the code clinic session in RFC3339 format.

    Returns:
    True if the user is booked as a volunteer for the code clinic session at the specified start time, False otherwise.

    Raises:
    None

    This function checks if a user is booked as a volunteer for a code clinic session at the specified start time.
    It searches for events at the given start time and iterates through the list of events.
    If the event is a code clinic session and the user is listed as an attendee, it returns True.
    If no matching event is found or if the user is not listed as an attendee, it returns False.

    Example:
    ```
    # Check if a user is booked as a volunteer for a code clinic session
    username = 'example_user'
    start_time = '2024-03-01T10:00:00Z'
    is_volunteer = is_volunteer(username, start_time)
    print(is_volunteer)
    ```
    """
    # Check if there is an event at the specified start_time in the volunteer slot
    events = search_time(start_time)
    for event in events:
        if 'attendees' in event:
            for attendee in event['attendees']:
                if attendee.get('email') == username + "@student.wethinkcode.co.za" and event['summary'] == 'Code Clinic Session':
                    return True
    return False


def cancel_volunteer_booking(service, username, start_time):
    """
    Cancels a volunteer booking for a code clinic session.

    Parameters:
    - service: An authenticated Google Calendar service object.
    - username: The username of the user attempting to cancel the volunteer booking.
    - start_time: The start time of the code clinic session in RFC3339 format.

    Returns:
    None

    Raises:
    None

    This function cancels a volunteer booking for a code clinic session.
    It retrieves the event ID associated with the specified start time.
    If an event is found, it deletes the event from the Google Calendar.
    If no event is found, it prints a message indicating that no volunteer booking was found.

    Example:
    ```
    from googleapiclient.discovery import build

    # Build Google Calendar service
    service = build('calendar', 'v3', credentials=credentials)

    # Cancel a volunteer booking
    username = 'example_user'
    start_time = '2024-03-01T10:00:00Z'
    cancel_volunteer_booking(service, username, start_time)
    ```
    """
    event_id = get_event_id(start_time)
    calendar_id = 'c_3b23a6dcc818ef6fc87099b492db10ff2c4b3d47036a1aede171bc1d19fb0059@group.calendar.google.com'
    
    if event_id:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        print('Volunteer booking canceled successfully')
    else:
        print('No volunteer booking found at the specified time.')

def cancel_volunteer_booking_command(service, args):
    """
    Cancels a volunteer booking for a code clinic session based on command-line arguments.

    Parameters:
    - service: An authenticated Google Calendar service object.
    - args: Command-line arguments containing username and start time.

    Returns:
    None

    Raises:
    None

    This function cancels a volunteer booking for a code clinic session based on the provided command-line arguments.
    It first checks if the provided arguments contain both username and start time.
    If both username and start time are provided, it verifies if the user is a volunteer using the `is_volunteer` function.
    If the user is a volunteer, it calls the `cancel_volunteer_booking` function to cancel the volunteer booking.
    If any of the required arguments are missing or if the user is not a volunteer, it prompts the user to enter the missing
    information or displays a message indicating the user is not authorized to cancel a volunteer booking.

    Example:
    ```
    from googleapiclient.discovery import build
    import argparse

    # Build Google Calendar service
    service = build('calendar', 'v3', credentials=credentials)

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Cancel volunteer booking for a code clinic session.')
    parser.add_argument('--username', type=str, help='Username of the user who booked the session')
    parser.add_argument('--start_time', type=str, help='Start time of the volunteering slot in RFC3339 format')
    args = parser.parse_args()

    # Cancel volunteer booking based on command-line arguments
    cancel_volunteer_booking_command(service, args)
    ```
    """
    if hasattr(args, 'username') and hasattr(args, 'start_time'):
        if is_volunteer(args.username, args.start_time):
            cancel_volunteer_booking(service, args.username, args.start_time)
            return
        else:
            print("You are not authorized to cancel a volunteer booking because you are not a volunteer.")
            return
    else:
        username = input("Please enter your username: ")
        start_time = input("Please enter the start time of the volunteering slot (YYYY-MM-DDTHH:MM:SS format): ")
        if is_volunteer(username, start_time):
            cancel_volunteer_booking(service, username, start_time)
        else:
            print("You are not authorized to cancel a volunteer booking because you are not a volunteer.")
