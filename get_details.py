from datetime import datetime as dt
import re
from dateutil import parser as date_parser

def get_email():
    """
    Prompts the user to enter an email and validates it.

    Returns:
    The full email address.

    Raises:
    None

    This function prompts the user to enter an email address and validates it using a basic regex pattern.
    It accepts any valid email format (name@domain.extension). If the entered email does not match the pattern,
    the user is prompted to enter it again until a valid email is provided.

    Example:
    ```
    # Get the email address
    email = get_email()
    print(email)  # Output: user@example.com
    ```
    """
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    email = input("Enter your email: ")
    
    # Validate email format
    while not re.match(email_pattern, email):
        email = input("Invalid email format. Please enter a valid email (e.g., user@example.com): ")

    return email


def get_decription():
    """
    Prompts the user to enter a description for the study session.

    Returns:
    The description provided by the user.

    Raises:
    None

    This function prompts the user to enter a description for the study session and returns the entered description.

    Example:
    ```
    # Get the description for the study session
    description = get_description()
    print(description)
    ```
    """
    summary=input('What do you want study: ')
    return summary

def is_valid_date(date_str):
    """
    Checks if a date string is valid and in the format YYYY-MM-DD.

    Parameters:
    - date_str: A string representing a date.

    Returns:
    True if the date string is valid and in the format YYYY-MM-DD, False otherwise.

    Raises:
    None

    This function attempts to parse the input date string using the datetime.strptime method with the format '%Y-%m-%d'.
    If the parsing is successful without raising a ValueError, it returns True, indicating that the date string is valid
    and in the correct format. Otherwise, if a ValueError is raised during parsing, it returns False.

    Example:
    ```
    # Check if a date string is valid
    date_string = '2024-03-01'
    is_valid = is_valid_date(date_string)
    print(is_valid)  # Output: True
    ```
    """
    try:
        dt.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False
    
def is_valid_time(time_str):
    """
    Checks if a time string is valid and falls within a specified range.

    Parameters:
    - time_str: A string representing a time in the format HH:MM.

    Returns:
    True if the time string is valid and falls within the range 08:00 to 16:30 (inclusive), with increments of 30 minutes,
    False otherwise.

    Raises:
    None

    This function attempts to split the input time string using the ':' delimiter and converts the hour and minute parts
    into integers. It then checks if the hour is between 8 and 16 (inclusive) and if the minute is either 0 or 30,
    representing increments of 30 minutes. If the time falls within the specified range and increments, it returns True,
    indicating that the time string is valid. Otherwise, if any parsing error occurs during conversion or if the time
    falls outside the specified range, it returns False.

    Example:
    ```
    # Check if a time string is valid
    time_string = '10:30'
    is_valid = is_valid_time(time_string)
    print(is_valid)  # Output: True
    ```
    """
    try:
        hour, minute = map(int, time_str.split(':'))
        return 8 <= hour <= 16 and (minute== 0 or minute == 30)
    except ValueError:
        return False

def get_date():
    """
    Prompts the user to enter a date in natural language (e.g., '23 march 2026') or YYYY-MM-DD format and validates it.

    Returns:
    The validated date string in YYYY-MM-DD format.

    Raises:
    None

    This function repeatedly prompts the user to enter a date until a valid date is provided.
    Accepts both natural language (e.g., "23 march 2026", "tomorrow", "next friday") and standard YYYY-MM-DD format.

    Example:
    ```
    # Get a valid date from the user
    date = get_date()
    print(date)  # Output: 2026-03-23
    ```
    """
    from dateutil import parser as date_parser
    
    while True:
        date_input = input("Enter date (e.g., '23 march 2026' or 'YYYY-MM-DD'): ").strip()
        
        try:
            # Try parsing natural language first
            parsed_date = date_parser.parse(date_input)
            result_date = parsed_date.strftime('%Y-%m-%d')
            
            # Validate it's a real date
            if is_valid_date(result_date):
                return result_date
            else:
                print("Invalid date. Please try again.")
        except (ValueError, date_parser.ParserError):
            # Try standard format
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date_input) and is_valid_date(date_input):
                return date_input
            else:
                print("Invalid date format. Try 'YYYY-MM-DD' or natural language like '23 march 2026'.")


def get_time():
    """
    Prompts the user to enter a time in the format HH:MM and validates it.

    Returns:
    The validated time string entered by the user, appended with seconds and timezone information.

    Raises:
    None

    This function repeatedly prompts the user to enter a time in the format HH:MM until a valid time is provided.
    It uses regular expressions to validate the format of the entered time string and the `is_valid_time` function
    to further validate if the time falls within the specified range. Once a valid time is entered, the function
    appends seconds and timezone information to the time string and returns it.

    Example:
    ```
    # Get a valid time from the user
    time = get_time()
    print(time)
    ```
    """
    while True:
        time = input("Enter Time in format HH:MM: ")
        if re.match(r'^\d{2}:\d{2}$', time) and is_valid_time(time):
            return time+":00+02:00"
        else:
            print("Invalid time format or invalid time. Please enter time in format HH:MM.")



