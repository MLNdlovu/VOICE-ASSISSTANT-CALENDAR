import unittest
from unittest.mock import patch, MagicMock
import os.path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from code_clinins_demo import (authenticate, #Mpilenhle: This is the first function I'm testing
                               config_command)  

class TestAuthenticate(unittest.TestCase):
    @patch('os.path.exists')
    @patch('google.oauth2.credentials.Credentials.from_authorized_user_file')
    @patch('google.oauth2.credentials.Credentials.refresh')
    @patch('google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file')
    @patch('builtins.open')
    def test_authenticate_success(self, mock_open, mock_flow, mock_refresh, mock_from_file, mock_path_exists):
        # Mocking file existence check
        mock_path_exists.return_value = True

        # Mocking Credentials.from_authorized_user_file to return mocked credentials
        mock_credentials = MagicMock(spec=Credentials)
        mock_from_file.return_value = mock_credentials

        # Mocking valid credentials
        mock_credentials.valid = True

        # Calling the authenticate function
        result = authenticate()

        # Assertions
        self.assertEqual(result, mock_credentials)

        # Ensure other mocks are not called
        self.assertFalse(mock_flow.called)
        self.assertFalse(mock_refresh.called)
        self.assertFalse(mock_open.called)

    @patch('google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file')
    @patch('builtins.open')
    @patch('webbrowser.open')
    @patch('code_clinins_demo.build')
    def test_config_command(self, mock_build, mock_webbrowser_open, mock_open, mock_from_client_secrets_file):
        SCOPES = ["https://www.googleapis.com/auth/calendar"]
        # Mocking the flow
        mock_flow = MagicMock()
        mock_from_client_secrets_file.return_value = mock_flow

        # Mocking the credentials and service
        mock_credentials = MagicMock()
        mock_service = MagicMock()
        mock_service.build.return_value = mock_service

        # Mocking the run_local_server method
        mock_flow.run_local_server.return_value = mock_credentials

        # Call the function
        config_command(None)

        # Assertions
        # Ensure InstalledAppFlow.from_client_secrets_file is called with the correct arguments
        mock_from_client_secrets_file.assert_called_once_with(
            os.getcwd() + "/.config/client_secret_372600977962-5tmobjbt9nv752ajec6tvrigjlfd4lpo.apps.googleusercontent.com.json",
            SCOPES
        )

        # Ensure run_local_server is called with the correct arguments
        mock_flow.run_local_server.assert_called_once_with(port=0, prompt="select_account")

        # Ensure webbrowser.open is called with the correct URL
        mock_webbrowser_open.assert_called_once_with(mock_flow.authorization_url(prompt='select_account')[0])

        # Ensure build is called with the correct arguments
        mock_build.assert_called_once_with("calendar", "v3", credentials=mock_credentials)

   
if __name__ == '__main__':
    unittest.main()
