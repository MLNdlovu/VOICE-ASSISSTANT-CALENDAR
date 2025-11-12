import unittest
from datetime import datetime as dt
from unittest.mock import patch
import re
from get_details import get_email, get_decription, is_valid_date, is_valid_time, get_date, get_time

class TestFunctions(unittest.TestCase):

    def test_get_email_valid(self):
        with patch('builtins.input', side_effect=['user@example.com']):
            self.assertEqual(get_email(), 'user@example.com')

    def test_get_description(self):
        with patch('builtins.input', return_value='This is a test description'):
            self.assertEqual(get_decription(), 'This is a test description')

    def test_is_valid_date_valid(self):
        self.assertTrue(is_valid_date('2024-03-01'))

    def test_is_valid_date_invalid(self):
        self.assertFalse(is_valid_date('2024-02-30'))

    def test_is_valid_time_valid(self):
        self.assertTrue(is_valid_time('10:30'))

    def test_is_valid_time_invalid(self):
        self.assertFalse(is_valid_time('17:00'))

    def test_get_date_valid(self):
        with patch('builtins.input', return_value='2024-03-01'):
            self.assertEqual(get_date(), '2024-03-01')

    def test_get_time_valid(self):
        with patch('builtins.input', return_value='12:30'):
            self.assertEqual(get_time(), '12:30:00+02:00')

if __name__ == '__main__':
    unittest.main()
