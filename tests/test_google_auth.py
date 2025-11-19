"""
Unit tests for googleAuth.py module.
Tests Google Workspace authentication and ChromeOS device retrieval.
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestBytesToGB(unittest.TestCase):
    """Tests for byte-to-gigabyte conversion utility."""

    def test_converts_bytes_to_gb(self):
        """Test conversion of bytes to GB."""
        from googleAuth import bytes_to_gb

        # 1 GB = 1024^3 bytes
        bytes_value = 1024 * 1024 * 1024
        result = bytes_to_gb(bytes_value)

        self.assertEqual(result, 1.0)

    def test_converts_megabytes_to_gb(self):
        """Test conversion of megabytes to GB."""
        from googleAuth import bytes_to_gb

        # 512 MB = 512 * 1024 * 1024 bytes
        bytes_value = 512 * 1024 * 1024
        result = bytes_to_gb(bytes_value)

        self.assertAlmostEqual(result, 0.5, places=5)

    def test_converts_zero_bytes(self):
        """Test conversion of zero bytes."""
        from googleAuth import bytes_to_gb

        result = bytes_to_gb(0)

        self.assertEqual(result, 0.0)

    def test_converts_large_bytes(self):
        """Test conversion of large byte values."""
        from googleAuth import bytes_to_gb

        # 10 GB
        bytes_value = 10 * 1024 * 1024 * 1024
        result = bytes_to_gb(bytes_value)

        self.assertEqual(result, 10.0)


class TestGoogleAuth(unittest.TestCase):
    """Tests for Google Workspace authentication."""

    @patch('googleAuth.service_account.Credentials.from_service_account_file')
    def test_auth_success(self, mock_from_file):
        """Test successful authentication."""
        from googleAuth import auth

        mock_creds = MagicMock()
        mock_delegated_creds = MagicMock()
        mock_creds.with_subject.return_value = mock_delegated_creds
        mock_from_file.return_value = mock_creds

        result = auth()

        self.assertEqual(result, mock_delegated_creds)
        mock_creds.with_subject.assert_called_once()

    @patch('googleAuth.service_account.Credentials.from_service_account_file')
    def test_auth_file_not_found(self, mock_from_file):
        """Test authentication when service account file not found."""
        from googleAuth import auth

        mock_from_file.side_effect = FileNotFoundError('File not found')

        result = auth()

        self.assertIsNone(result)

    @patch('googleAuth.service_account.Credentials.from_service_account_file')
    def test_auth_generic_exception(self, mock_from_file):
        """Test authentication exception handling."""
        from googleAuth import auth

        mock_from_file.side_effect = Exception('Invalid credentials')

        result = auth()

        self.assertIsNone(result)

    @patch('googleAuth.service_account.Credentials.from_service_account_file')
    def test_auth_includes_scopes(self, mock_from_file):
        """Test that authentication includes required scopes."""
        from googleAuth import auth

        mock_creds = MagicMock()
        mock_creds.with_subject.return_value = MagicMock()
        mock_from_file.return_value = mock_creds

        auth()

        # Check that scopes were included
        call_kwargs = mock_from_file.call_args[1]
        self.assertIn('scopes', call_kwargs)
        self.assertIn('https://www.googleapis.com/auth/admin.directory.device.chromeos',
                      call_kwargs['scopes'])


class TestFetchChromeOSDevices(unittest.TestCase):
    """Tests for ChromeOS device fetching."""

    @patch('googleAuth.auth')
    @patch('googleAuth.build')
    def test_fetch_devices_success(self, mock_build, mock_auth):
        """Test successful device fetching."""
        from googleAuth import fetch_and_print_chromeos_devices

        # Mock credentials
        mock_creds = MagicMock()
        mock_auth.return_value = mock_creds

        # Mock service and API response
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_devices_resource = MagicMock()
        mock_service.chromeosdevices.return_value = mock_devices_resource

        mock_list_result = MagicMock()
        mock_devices_resource.list.return_value = mock_list_result

        mock_list_result.execute.return_value = {
            'chromeosdevices': [
                {
                    'serialNumber': 'SN001',
                    'status': 'ACTIVE',
                    'model': 'Dell Chromebook 11',
                    'recentUsers': [{'email': 'user@example.com'}],
                    'macAddress': 'a8:1d:16:67:42:f7',
                    'lastKnownNetwork': [{'ipAddress': '192.168.1.100'}],
                    'activeTimeRanges': [{'date': '2024-01-15'}],
                    'autoUpdateThrough': '2025-06-15'
                }
            ]
        }

        result = fetch_and_print_chromeos_devices()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['Serial Number'], 'SN001')
        self.assertEqual(result[0]['Device User'], 'user@example.com')
        self.assertEqual(result[0]['Status'], 'ACTIVE')

    @patch('googleAuth.auth')
    @patch('googleAuth.build')
    def test_fetch_devices_with_pagination(self, mock_build, mock_auth):
        """Test device fetching with pagination."""
        from googleAuth import fetch_and_print_chromeos_devices

        mock_creds = MagicMock()
        mock_auth.return_value = mock_creds

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_devices_resource = MagicMock()
        mock_service.chromeosdevices.return_value = mock_devices_resource

        # Mock two pages of results
        mock_list_result = MagicMock()
        mock_devices_resource.list.return_value = mock_list_result

        page1 = {
            'chromeosdevices': [
                {
                    'serialNumber': 'SN001',
                    'status': 'ACTIVE',
                    'model': 'Dell Chromebook 11',
                    'recentUsers': [{'email': 'user1@example.com'}],
                    'macAddress': 'a8:1d:16:67:42:f7',
                    'lastKnownNetwork': [{'ipAddress': '192.168.1.100'}],
                    'activeTimeRanges': [{'date': '2024-01-15'}],
                    'autoUpdateThrough': '2025-06-15'
                }
            ],
            'nextPageToken': 'page2token'
        }

        page2 = {
            'chromeosdevices': [
                {
                    'serialNumber': 'SN002',
                    'status': 'ACTIVE',
                    'model': 'ASUS Chromebook',
                    'recentUsers': [{'email': 'user2@example.com'}],
                    'macAddress': 'b8:2d:26:68:52:f8',
                    'lastKnownNetwork': [{'ipAddress': '192.168.1.101'}],
                    'activeTimeRanges': [{'date': '2024-01-14'}],
                    'autoUpdateThrough': '2025-07-15'
                }
            ]
        }

        mock_list_result.execute.side_effect = [page1, page2]

        result = fetch_and_print_chromeos_devices()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['Serial Number'], 'SN001')
        self.assertEqual(result[1]['Serial Number'], 'SN002')

    @patch('googleAuth.auth')
    @patch('googleAuth.build')
    def test_fetch_devices_empty_result(self, mock_build, mock_auth):
        """Test device fetching when no devices returned."""
        from googleAuth import fetch_and_print_chromeos_devices

        mock_creds = MagicMock()
        mock_auth.return_value = mock_creds

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_devices_resource = MagicMock()
        mock_service.chromeosdevices.return_value = mock_devices_resource

        mock_list_result = MagicMock()
        mock_devices_resource.list.return_value = mock_list_result

        mock_list_result.execute.return_value = {'chromeosdevices': []}

        result = fetch_and_print_chromeos_devices()

        self.assertEqual(len(result), 0)

    @patch('googleAuth.auth')
    def test_fetch_devices_auth_fails(self, mock_auth):
        """Test device fetching when authentication fails."""
        from googleAuth import fetch_and_print_chromeos_devices

        mock_auth.return_value = None

        result = fetch_and_print_chromeos_devices()

        self.assertEqual(len(result), 0)

    @patch('googleAuth.auth')
    @patch('googleAuth.build')
    def test_fetch_devices_api_error(self, mock_build, mock_auth):
        """Test device fetching when API call raises exception."""
        from googleAuth import fetch_and_print_chromeos_devices

        mock_creds = MagicMock()
        mock_auth.return_value = mock_creds

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_devices_resource = MagicMock()
        mock_service.chromeosdevices.return_value = mock_devices_resource

        mock_list_result = MagicMock()
        mock_devices_resource.list.return_value = mock_list_result

        mock_list_result.execute.side_effect = Exception('API error')

        result = fetch_and_print_chromeos_devices()

        self.assertEqual(len(result), 0)

    @patch('googleAuth.auth')
    @patch('googleAuth.build')
    def test_fetch_devices_handles_missing_fields(self, mock_build, mock_auth):
        """Test device fetching handles missing optional fields."""
        from googleAuth import fetch_and_print_chromeos_devices

        mock_creds = MagicMock()
        mock_auth.return_value = mock_creds

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_devices_resource = MagicMock()
        mock_service.chromeosdevices.return_value = mock_devices_resource

        mock_list_result = MagicMock()
        mock_devices_resource.list.return_value = mock_list_result

        # Device with missing optional fields
        mock_list_result.execute.return_value = {
            'chromeosdevices': [
                {
                    'serialNumber': 'SN001',
                    'status': 'ACTIVE',
                    # Missing model, recentUsers, etc.
                }
            ]
        }

        result = fetch_and_print_chromeos_devices()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['Serial Number'], 'SN001')
        self.assertIsNone(result[0]['Device User'])
        self.assertIsNone(result[0]['Model'])

    @patch('googleAuth.auth')
    @patch('googleAuth.build')
    def test_fetch_devices_respects_config_page_size(self, mock_build, mock_auth):
        """Test that device fetching respects configured page size."""
        from googleAuth import fetch_and_print_chromeos_devices

        mock_creds = MagicMock()
        mock_auth.return_value = mock_creds

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_devices_resource = MagicMock()
        mock_service.chromeosdevices.return_value = mock_devices_resource

        mock_list_result = MagicMock()
        mock_devices_resource.list.return_value = mock_list_result

        mock_list_result.execute.return_value = {'chromeosdevices': []}

        fetch_and_print_chromeos_devices()

        # Verify list was called with pagination parameters
        mock_devices_resource.list.assert_called_once()
        call_kwargs = mock_devices_resource.list.call_args[1]
        self.assertIn('maxResults', call_kwargs)
        self.assertEqual(call_kwargs['customerId'], 'my_customer')

    @patch('googleAuth.auth')
    @patch('googleAuth.build')
    def test_fetch_devices_maps_all_fields(self, mock_build, mock_auth):
        """Test that all device fields are correctly mapped."""
        from googleAuth import fetch_and_print_chromeos_devices

        mock_creds = MagicMock()
        mock_auth.return_value = mock_creds

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_devices_resource = MagicMock()
        mock_service.chromeosdevices.return_value = mock_devices_resource

        mock_list_result = MagicMock()
        mock_devices_resource.list.return_value = mock_list_result

        mock_list_result.execute.return_value = {
            'chromeosdevices': [
                {
                    'serialNumber': 'SN001',
                    'status': 'ACTIVE',
                    'model': 'Dell Chromebook 11',
                    'recentUsers': [{'email': 'user@example.com'}],
                    'macAddress': 'a8:1d:16:67:42:f7',
                    'lastKnownNetwork': [{'ipAddress': '192.168.1.100'}],
                    'activeTimeRanges': [{'date': '2024-01-15'}],
                    'firstEnrollmentTime': '2023-01-15T10:00:00.000Z',
                    'lastSync': '2024-01-15T10:00:00.000Z',
                    'autoUpdateThrough': '2025-06-15'
                }
            ]
        }

        result = fetch_and_print_chromeos_devices()

        device = result[0]
        self.assertEqual(device['Serial Number'], 'SN001')
        self.assertEqual(device['Status'], 'ACTIVE')
        self.assertEqual(device['Model'], 'Dell Chromebook 11')
        self.assertEqual(device['Device User'], 'user@example.com')
        self.assertEqual(device['Mac Address'], 'a8:1d:16:67:42:f7')
        self.assertEqual(device['Last Known IP Address'], '192.168.1.100')
        self.assertEqual(device['EOL'], '2025-06-15')


if __name__ == '__main__':
    unittest.main()
