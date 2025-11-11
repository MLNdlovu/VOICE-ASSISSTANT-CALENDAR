from datetime import datetime as dt
import re

def get_email():
    """
    Prompts the user to enter an email and validates it.

    Returns:
    The full email address (not just the username).

    Raises:
    None

    This function prompts the user to enter an email address and validates it by checking if it ends with
    either '@student.wethinkcode.co.za' or '@gmail.com'. If the entered email does not match either pattern,
    the user is prompted to enter it again until a valid email is provided. Once a valid email is entered,
    the function returns the full email address.

    Example:
    ```
    # Get the email address
    email = get_email()
    print(email)  # Output: lungelondlovu194@gmail.com
    ```
    """
    email=input("enter email: ")
    
    # Check if email ends with either student email or gmail
    valid_email = (email.endswith("@student.wethinkcode.co.za") or 
                   email.endswith("@gmail.com"))
    
    while not valid_email:
        email=input("enter email: ")
        valid_email = (email.endswith("@student.wethinkcode.co.za") or 
                       email.endswith("@gmail.com"))

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
    Prompts the user to enter a date in the format YYYY-MM-DD and validates it.

    Returns:
    The validated date string entered by the user.

    Raises:
    None

    This function repeatedly prompts the user to enter a date in the format YYYY-MM-DD until a valid date is provided.
    It uses regular expressions to validate the format of the entered date string and the `is_valid_date` function
    to further validate if the date is a valid calendar date. Once a valid date is entered, the function returns the date.

    Example:
    ```
    # Get a valid date from the user
    date = get_date()
    print(date)
    ```
    """
    while True:
        date = input("Enter Date in format YYYY-MM-DD: ")
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date) and is_valid_date(date):
            return date
        else:
            print("Invalid date format. Please enter date in format YYYY-MM-DD.")


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



