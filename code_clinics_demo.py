import os.path
import argparse
import datetime
import sys
import webbrowser
import json
from prettytable import PrettyTable
import book
import get_details

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

Calendar_ID='c_3b23a6dcc818ef6fc87099b492db10ff2c4b3d47036a1aede171bc1d19fb0059@group.calendar.google.com'

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Constant for the shared calendar name
SHARED_CALENDAR_NAME = "Code Clinics T12"


def authenticate():
    """
    Authenticates the user and retrieves the Google Calendar API credentials.

    Returns:
    An authenticated Google Calendar service object.

    Raises:
    None

    This function attempts to retrieve the user's Google Calendar API credentials.
    It first checks if the credentials file exists locally. If found, it loads the credentials.
    If the loaded credentials are not valid or have expired, it attempts to refresh the token.
    If the token cannot be refreshed, it initiates the OAuth 2.0 authorization flow to obtain new credentials.
    The obtained credentials are then saved locally for future use. Finally, it returns the authenticated
    Google Calendar service object.

    Example:
    ```
    # Authenticate the user and obtain Google Calendar service object
    service = authenticate()
    ```
    """
    creds = None
    
    if os.path.exists(".config/token.json"):
        creds = Credentials.from_authorized_user_file(".config/token.json", SCOPES)

    if not creds or not creds.valid:
        try:
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing token...")
                creds.refresh(Request())
            else:
                client_secret_path = os.path.join(os.getcwd(), ".config", "client_secret_372600977962-5tmobjbt9nv752ajec6tvrigjlfd4lpo.apps.googleusercontent.com.json")
                flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
                creds = flow.run_local_server(port=0)

                # Saves the credentials for the next run
                with open(".config/token.json", "w") as token:
                    token.write(creds.to_json())
                print("New token obtained.")

        except Exception as e:
            print(f"Error during authentication: {e}")
            creds = None

    return creds


def display_events_prettytable(events):
    """
    Displays events in a formatted PrettyTable.

    Parameters:
    - events: A list of event dictionaries containing event details.

    Returns:
    None

    Raises:
    None

    This function takes a list of event dictionaries as input and formats them into a PrettyTable.
    It adds the event details such as Date, Event Name, and Creator Email to the table.
    The Date is extracted from the event dictionary's "start" key, and the creator's email is extracted from
    the event dictionary's "creator" key.
    The resulting PrettyTable is then printed to the console.

    Example:
    ```
    # Display events in a formatted PrettyTable
    events = [
        {"start": {"dateTime": "2024-03-01T10:00:00Z"}, "summary": "Code Clinic Session", "creator": {"email": "example@example.com"}},
        {"start": {"dateTime": "2024-03-02T11:00:00Z"}, "summary": "Study Group Meeting", "creator": {"email": "another@example.com"}}
    ]
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

    # Sets the format to a pretty table using PrettyTable library
    table.border = True
    table.header = True
    table.hrules = 1 # PrettyTable.ALL to display horizontal lines
    table.vrules = 0 # PrettyTable.ALL to display vertical lines

    print(table)

def config_command(args):
    """
    Configures the Google Calendar API authentication and obtains the necessary credentials.

    Parameters:
    - args: Command-line arguments (not used in this function).

    Returns:
    None

    Raises:
    None

    This function configures the Google Calendar API authentication by initiating the OAuth 2.0 authorization flow.
    It loads the client secrets file and uses it to create an InstalledAppFlow object.
    The user is prompted to authenticate and grant permission via the default web browser.
    Upon successful authentication, the function obtains the credentials and creates the Google Calendar service object.
    It then prints the ID of the shared calendar obtained from the configuration.

    Example:
    ```
    # Configure the Google Calendar API authentication
    config_command(args)
    ```
    """   

    flow = InstalledAppFlow.from_client_secrets_file(
os.getcwd()+"/.config/client_secret_372600977962-5tmobjbt9nv752ajec6tvrigjlfd4lpo.apps.googleusercontent.com.json",SCOPES
)

    try:
    # Run the local server and get the credentials
        credentials = flow.run_local_server(port=0, prompt="select_account")

        # Open the authentication URL in the default web browser
        webbrowser.open(flow.authorization_url(prompt='select_account')[0])
        print("Please follow the link to authenticate and grant permission.")

        # Create the service object using the obtained credentials
        service = build("calendar", "v3", credentials=credentials)

        # Example: Create or get an existing calendar named "code_clinics_demo"
        calendar_id =Calendar_ID
        print(f"Calendar '{SHARED_CALENDAR_NAME}' obtained with ID: {calendar_id}")

    except Exception as e:
        print(f"Error running local server: {e}")


def events_command(args):
    """
    Retrieves upcoming events from the configured Google Calendar and displays them.

    Parameters:
    - args: Command-line arguments (not used in this function).

    Returns:
    None

    Raises:
    None

    This function authenticates the user, obtains the necessary credentials, and creates a Google Calendar service object.
    It then retrieves upcoming events from the configured calendar using the Google Calendar API.
    The upcoming events are fetched for the next 7 days and displayed in a formatted PrettyTable.
    If no events are found, a message indicating the absence of upcoming events is printed.

    Example:
    ```
    # Retrieve and display upcoming events from the configured Google Calendar
    events_command(args)
    ```
    """
    creds = authenticate()
    service = build("calendar", "v3", credentials=creds)

    # Obtain the calendar ID
    calendar_id = Calendar_ID

    # Retrieve upcoming events
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print("\nGetting the upcoming 7 events\n")
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
        return

    # Display events in a PrettyTable format
    display_events_prettytable(events)

def load_code_clinics_calendar(service):
    """
    Retrieves events from the Google Calendar associated with code clinics and saves them to a local JSON file.

    Parameters:
    - service: An authenticated Google Calendar service object.

    Returns:
    None

    Raises:
    None

    This function retrieves events from the Google Calendar associated with code clinics using the provided
    Google Calendar service object. It then saves the events to a local JSON file named 'code_clinics_calendar.json'.
    If no events are found, an empty JSON array is written to the file.

    Example:
    ```
    # Authenticate the user and obtain Google Calendar service object
    service = authenticate()

    # Load events from the code clinics calendar and save them to a local JSON file
    load_code_clinics_calendar(service)
    ```
    """ 
    calendar_id = 'c_3b23a6dcc818ef6fc87099b492db10ff2c4b3d47036a1aede171bc1d19fb0059@group.calendar.google.com'
    events_result = service.events().list(calendarId=calendar_id).execute()
    events = events_result.get('items', [])

    
    with open('code_clinics_calendar.json', 'w') as f:
        json.dump(events, f, indent=4)


def help_command(args):
    """
    Displays a list of available commands and their descriptions.

    Parameters:
    - args: Command-line arguments (not used in this function).

    Returns:
    None

    Raises:
    None

    This function prints a list of available commands along with their descriptions to the console.
    Each command is listed with a brief description of its functionality.

    Example:
    ```
    # Display a list of available commands and their descriptions
    help_command(args)
    ```
    """
    print("Available commands:")
    print("- help: Display this help message")
    print("- config: Open the authentication URL in the default web browser")
    print("- book: Book a slot")
    print("- volunteer: Volunteer for an event")
    print("- cancel-book: Cancel a booking")
    print("- cancel-volunteer: Cancel volunteering")
    print("- share-calendar: Share the calendar with a tester")
    print("- events: Display the next seven events")


def share_calendar_command(service, args):
    """
    Provides instructions for sharing the user's calendar with Code Clinics.
    
    Parameters:
    - service: An authenticated Google Calendar service object.
    - args: Command arguments (not used).
    
    Returns:
    None
    
    This function displays step-by-step instructions for users to share their personal
    calendar with the Code Clinics application so that their availability can be viewed.
    """
    print("\n" + "="*60)
    print("HOW TO SHARE YOUR CALENDAR WITH CODE CLINICS")
    print("="*60)
    
    print("\n📅 STEP 1: Subscribe to Code Clinics Calendar")
    print("-" * 60)
    print("1. Go to Google Calendar: https://calendar.google.com")
    print("2. On the left sidebar, find 'Other calendars'")
    print("3. Click the '+' button next to 'Other calendars'")
    print("4. Select 'Subscribe to calendar'")
    print("5. Enter this calendar ID:")
    print(f"   {Calendar_ID}")
    print("6. Click 'Subscribe'")
    
    print("\n📤 STEP 2: Share YOUR Calendar with Code Clinics")
    print("-" * 60)
    print("1. Go to Google Calendar: https://calendar.google.com")
    print("2. On the left sidebar, find your calendar name")
    print("3. Click the three dots menu next to your calendar")
    print("4. Select 'Settings and sharing'")
    print("5. Scroll down to 'Share with specific people'")
    print("6. Click 'Add people'")
    print("7. Enter this service account email:")
    print("   c_3b23a6dcc818ef6fc87099b492db10ff2c4b3d47036a1aede171bc1d19fb0059@group.calendar.google.com")
    print("8. Select permission level: 'Viewer' or 'Editor'")
    print("9. Click 'Send'")
    
    print("\n✅ STEP 3: Make Calendar Public (Optional)")
    print("-" * 60)
    print("Alternatively, you can make your calendar public:")
    print("1. Go to Settings and sharing (from Step 2)")
    print("2. Under 'Access permissions for events'")
    print("3. Check 'Make available to public'")
    print("4. Choose sharing settings")
    
    print("\n" + "="*60)
    print("Once shared, the system will be able to view your availability!")
    print("="*60 + "\n")


def main():
    creds = authenticate()
    service = build("calendar", "v3", credentials=creds)
    load_code_clinics_calendar(service)
    while True:
        print("Available commands: help, config, book, volunteer, cancel-book, cancel-volunteer, share-calendar, events, exit")
        command = input("Enter a command: ")
        
        if command == "exit":
            break
        
        parser = argparse.ArgumentParser(description="Code Clinics Demo Calendar Management")
        parser.add_argument("command", choices=["help", "config", "book", "volunteer", "cancel-book", "cancel-volunteer", "share-calendar", "events"], help="Command to execute")
        
        args = parser.parse_args([command])

        if args.command == "help":
            help_command(args)
        elif args.command == "config":
            config_command(args)
        elif args.command == "book":
            
            user_name=get_details.get_email()
            book_date=get_details.get_date()
            book_time=get_details.get_time()
            slot_time=book_date+"T"+book_time
            summary=get_details.get_decription()
            book.book_as_student(service,user_name,slot_time,summary)
            load_code_clinics_calendar(service)
        
        elif args.command == "volunteer":
            # volunteer_command(args)
            user_name=get_details.get_email()
            book_date=get_details.get_date()
            book_time=get_details.get_time()
            slot_time=book_date+"T"+book_time
        
            book.book_as_volunteer(service,user_name,slot_time)
            load_code_clinics_calendar(service)
            
        elif args.command == "cancel-book":
            # cancel_command(args)
            user_name = get_details.get_email()
            start_date = get_details.get_date()
            start_time = get_details.get_time()
            start_datetime = f"{start_date}T{start_time}"
            book.cancel_booking_command(service, argparse.Namespace(username=user_name, start_time=start_datetime))
            
        elif args.command == "cancel-volunteer":
            # cancel_volunteer_command(args)
            user_name = get_details.get_email()
            start_date = get_details.get_date()
            start_time = get_details.get_time()
            start_datetime = f"{start_date}T{start_time}"
            if book.is_volunteer(user_name, start_datetime):
        # Proceed with canceling the volunteer booking
                book.cancel_volunteer_booking_command(service, argparse.Namespace(username=user_name, start_time=start_datetime))
            else:
        # Display message indicating the user is not authorized to cancel a volunteer booking
                print("You are not authorized to cancel a volunteer booking because you are not a volunteer.")
            
        elif args.command == "share-calendar":
            share_calendar_command(service, args)
        elif args.command == "events":
            events_command(args)
        else:
            print(f"Unknown command: {args.command}")
            
if __name__ == "__main__":
        main()
