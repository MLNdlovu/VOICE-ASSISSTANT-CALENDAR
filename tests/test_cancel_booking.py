import unittest
from unittest.mock import MagicMock, patch, call
from book import cancel_booking, cancel_booking_command


class TestBookingFunctions(unittest.TestCase):

    @patch('builtins.print')
    @patch('src.book.get_event_id', return_value='mock_event_id')
    def test_cancel_booking_success(self, mock_get_event_id, mock_print):
        mock_service = MagicMock()
        mock_service.events().delete().execute.return_value = None

        cancel_booking(mock_service, 'test_user', '2022-02-14T10:00:00')

        # Verify the correct print message was shown
        mock_print.assert_called_once_with('Booking canceled successfully')

    @patch('builtins.print')
    @patch('src.book.get_event_id', return_value=None)
    def test_cancel_booking_no_booking_found(self, mock_get_event_id, mock_print):
        mock_service = MagicMock()

        cancel_booking(mock_service, 'test_user', '2022-02-14T10:00:00')

        # Verify the "not found" message was shown
        mock_print.assert_called_once_with('No booking found at the specified time.')


if __name__ == '__main__':
    unittest.main()
