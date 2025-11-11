import unittest
from unittest.mock import MagicMock, patch
from book import cancel_booking, cancel_booking_command, is_volunteer, cancel_volunteer_booking, cancel_volunteer_booking_command

class TestBookingFunctions(unittest.TestCase):

    @patch('book.get_event_id', return_value='mock_event_id')
    @patch('book.print')
    def test_cancel_booking_success(self, mock_print, mock_get_event_id):
        mock_service = MagicMock()
        mock_service.events().delete().execute.return_value = None

        cancel_booking(mock_service, 'test_user', '2022-02-14T10:00:00')

        mock_print.assert_called_once_with('Booking canceled successfully')

    @patch('book.get_event_id', return_value=None)
    @patch('book.print')
    def test_cancel_booking_no_booking_found(self, mock_print, mock_get_event_id):
        mock_service = MagicMock()

        cancel_booking(mock_service, 'test_user', '2022-02-14T10:00:00')

        mock_print.assert_called_once_with('No booking found at the specified time.')

    @patch('book.is_volunteer', return_value=True)
    @patch('book.get_event_id', return_value='mock_event_id')
    @patch('book.print')
    def test_cancel_volunteer_booking_success(self, mock_print, mock_get_event_id, mock_is_volunteer):
        mock_service = MagicMock()
        mock_service.events().delete().execute.return_value = None

        cancel_volunteer_booking(mock_service, 'test_user', '2022-02-14T10:00:00')

        mock_print.assert_called_once_with('Volunteer booking canceled successfully')

    @patch('book.is_volunteer', return_value=False)
    @patch('book.get_event_id', return_value='mock_event_id')
    @patch('book.print')
    def test_cancel_volunteer_booking_not_authorized(self, mock_print, mock_get_event_id, mock_is_volunteer):
        mock_service = MagicMock()

        cancel_volunteer_booking(mock_service, 'test_user', '2022-02-14T10:00:00')

        mock_print.assert_called_once_with('Volunteer booking canceled successfully')

    @patch('builtins.input', side_effect=['test_user', '2022-02-14T10:00:00'])
    @patch('book.is_volunteer', return_value=True)
    @patch('book.get_event_id', return_value='mock_event_id')
    @patch('book.print')
    def test_cancel_volunteer_booking_command_success(self, mock_print, mock_get_event_id, mock_is_volunteer, mock_input):
        mock_service = MagicMock()
        mock_service.events().delete().execute.return_value = None

        cancel_volunteer_booking_command(mock_service, MagicMock())

        mock_print.assert_called_once_with('Volunteer booking canceled successfully')

    @patch('builtins.input', side_effect=['test_user', '2022-02-14T10:00:00'])
    @patch('book.is_volunteer', return_value=False)
    @patch('book.get_event_id', return_value='mock_event_id')
    @patch('book.print')
    def test_cancel_volunteer_booking_command_not_authorized(self, mock_print, mock_get_event_id, mock_is_volunteer, mock_input):
        mock_service = MagicMock()

        cancel_volunteer_booking_command(mock_service, MagicMock())

        mock_print.assert_called_once_with('You are not authorized to cancel a volunteer booking because you are not a volunteer.')

if __name__ == '__main__':
    unittest.main()
