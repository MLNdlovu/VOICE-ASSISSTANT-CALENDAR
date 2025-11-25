# View calendar events
# Display student/user calendar events

import datetime
from prettytable import PrettyTable
from googleapiclient.errors import HttpError


def view_student_event(service, username):
    """
    Retrieves and displays upcoming events from the calendar associated with the provided student's username.

    Parameters:
    - service: An authenticated Google Calendar service object.
    - username: The username of the student whose calendar events are to be viewed.

    Returns:
    None

    Raises:
    None

    This function retrieves upcoming events from the calendar associated with the provided student's username.
    It uses the provided Google Calendar service object to access the calendar data.
    The upcoming events are fetched for the next 7 days and displayed to the console.
    If no events are found, a message indicating the absence of upcoming events is printed.

    Example:
    ```
    # Authenticate the user and obtain Google Calendar service object
    service = authenticate()

    # View upcoming events for the student with the specified username
    view_student_event(service, "example_username")
    ```
    """
    # Support both student and gmail accounts
    if username.endswith("@"):
        calendar_id = username
    elif "@" in username:
        calendar_id = username
    else:
        calendar_id = username + '@student.wethinkcode.co.za'

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    end_date = (datetime.datetime.now() + datetime.timedelta(days=7)).isoformat()
    print(f"\nGetting {calendar_id} upcoming events\n")
    
    try:
        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=now,
                maxResults=7,
                singleEvents=True,
                orderBy="startTime",
                timeZone='Africa/Johannesburg',
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            print("No upcoming events found.")

        # Display events in a PrettyTable format
        display_events_prettytable(events)
    
    except HttpError as e:
        if e.resp.status == 404:
            print(f"Calendar not found for {calendar_id}. The user may not have shared their calendar or the email doesn't exist.")
        else:
            print(f"An error occurred: {e}")


def view_upcoming_events(service):
    """
    Retrieves and displays upcoming events from the user's calendar.

    Parameters:
    - service: An authenticated Google Calendar service object.

    Returns:
    None

    Raises:
    None

    This function retrieves upcoming events from the user's calendar using the provided Google Calendar service object.
    It then displays the retrieved events to the console. If no events are found, a message indicating the absence of
    upcoming events is printed.

    Example:
    ```
    # Authenticate the user and obtain Google Calendar service object
    service = authenticate()

    # View upcoming calendar events
    view_upcoming_events(service)
    ```
    """
    try:
            # Get the user's primary calendar
            calenderId='primary'
            # Define parameters for the events list request
            events_result = service.events().list(calendarId=calenderId).execute()
            events = events_result.get('items', [])

            # Handle the results here
            if not events:
                print('No upcoming events found.')
            else:
                print('Upcoming Calendar Events:')
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    # print(f'{event["summary"]} ({start})')
            display_events_prettytable(events)
    except Exception as e:
            print("Error:", e)


def view_code_clinics(service):
    """Deprecated: Use view_upcoming_events instead."""
    return view_upcoming_events(service)


def display_events_prettytable(events):
    
    """
    Displays events in a formatted PrettyTable.

    Parameters:
    - events: A list of dictionaries representing events, with keys "start" (containing the event's start date/time),
              "summary" (containing the event name), and "creator" (containing the creator's email).

    Returns:
    None

    Raises:
    None

    This function takes a list of events and formats them into a PrettyTable, with columns for Date, Event Name,
    and Creator Email. The events are iterated through, and their details are added to the table row by row.
    The resulting PrettyTable is then printed to the console.

    Example:
    ```
    # Define a list of events
    events = [
        {"start": {"dateTime": "2024-03-01T10:00:00Z"}, "summary": "Calendar Meeting", "creator": {"email": "example@example.com"}},
        {"start": {"dateTime": "2024-03-02T11:00:00Z"}, "summary": "Team Meeting", "creator": {"email": "another@example.com"}}
    ]

    # Display events in a formatted PrettyTable
    display_events_prettytable(events)
    ```
    """
    table = PrettyTable()
    table.field_names = ["Date", "Event Name", "Creator Email"]
    table.align["Date"] = "l" # Left-align the Date column
    table.align["Event Name"] = "l" # Left-align the Event Name column
    table.align["Creator Email"] = "l" # Left-align the Creator Email column

    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        creator_email = event.get("creator", {}).get("email", "N/A")
        table.add_row([start, event["summary"], creator_email])

    # Set the format to a pretty table
    table.border = True
    table.header = True
    table.hrules = 1 # PrettyTable.ALL to display horizontal lines
    table.vrules = 0 # PrettyTable.ALL to display vertical lines

    print(table)
