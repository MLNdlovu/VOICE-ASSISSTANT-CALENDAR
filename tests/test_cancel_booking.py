import unittest
from unittest.mock import MagicMock, patch
from book import cancel_booking, cancel_booking_command

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

    # Volunteer-related tests removed because volunteer functionality has been disabled.

if __name__ == '__main__':
    unittest.main()
