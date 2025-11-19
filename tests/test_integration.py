"""
Integration and CLI tests for Google2Snipe-IT.
Tests full workflows and end-to-end scenarios with mocked external dependencies.
"""

import unittest
import sys
import types
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import importlib.util

# Setup mock modules for imports
for name in ['googleAuth', 'gemini']:
    sys.modules.setdefault(name, types.ModuleType(name))

# Dummy dotenv
dotenv_mod = types.ModuleType('dotenv')
setattr(dotenv_mod, 'load_dotenv', lambda *args, **kwargs: None)
sys.modules['dotenv'] = dotenv_mod

# Dummy tqdm
tqdm_mod = types.ModuleType('tqdm')
setattr(tqdm_mod, 'tqdm', lambda *args, **kwargs: (x for x in args[0]) if args else [])
setattr(tqdm_mod, 'write', lambda *args, **kwargs: None)
sys.modules['tqdm'] = tqdm_mod

# Mock requests
sys.modules['requests'] = MagicMock()

MODULE_PATH = Path(__file__).resolve().parents[1] / 'snipe-IT.py'
spec = importlib.util.spec_from_file_location('snipe_it', MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

create_hardware = module.create_hardware
update_hardware = module.update_hardware
format_mac = module.format_mac


class TestHardwareCreationWorkflow(unittest.TestCase):
    """Tests for complete hardware creation workflow."""

    @patch('snipe_it.get_model_id')
    @patch('snipe_it.get_status_id')
    @patch('snipe_it.retry_request')
    def test_create_new_hardware_success(self, mock_retry, mock_status_id, mock_model_id):
        """Test creating a new hardware asset successfully."""
        mock_status_id.return_value = 2
        mock_model_id.return_value = 42

        # Mock successful creation response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'payload': {'id': 100, 'asset_tag': 'TAG001'}
        }
        mock_retry.return_value = mock_response

        status_code, result = create_hardware(
            asset_tag='TAG001',
            status_name='ACTIVE',
            model_name='Dell Latitude 7420',
            macAddress='a81d166742f7',
            createdDate='2024-01-15',
            userEmail='user@example.com',
            ipAddress='192.168.1.100'
        )

        self.assertEqual(status_code, 200)
        self.assertEqual(result['status'], 'success')

    @patch('snipe_it.get_model_id')
    @patch('snipe_it.get_status_id')
    @patch('snipe_it.retry_request')
    def test_create_hardware_with_duplicate_asset_tag(self, mock_retry, mock_status_id, mock_model_id):
        """Test creating hardware detects and updates duplicates."""
        mock_status_id.return_value = 2
        mock_model_id.return_value = 42

        # Mock duplicate error response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'error',
            'messages': {'asset_tag': ['Asset tag already exists']}
        }
        mock_retry.return_value = mock_response

        # Should trigger update_hardware instead
        with patch('snipe_it.update_hardware') as mock_update:
            status_code, result = create_hardware(
                asset_tag='TAG001',
                status_name='ACTIVE',
                model_name='Dell Latitude 7420',
                macAddress='a81d166742f7',
                createdDate='2024-01-15'
            )

            # Verify update was called
            mock_update.assert_called_once()

    @patch('snipe_it.get_model_id')
    @patch('snipe_it.get_status_id')
    @patch('snipe_it.gemini')
    @patch('snipe_it.get_category_id')
    @patch('snipe_it.assign_fieldset_to_model')
    @patch('snipe_it.retry_request')
    def test_create_hardware_with_new_model(self, mock_retry, mock_assign, mock_category_id,
                                            mock_gemini, mock_status_id, mock_model_id):
        """Test creating hardware with a new model."""
        mock_status_id.return_value = 2
        mock_model_id.return_value = None  # Model doesn't exist

        # Mock Gemini response for categorization
        mock_gemini_response = Mock()
        mock_gemini_response.text = '**Laptops**'
        mock_gemini.gemini_prompt.return_value = mock_gemini_response

        mock_category_id.return_value = 5

        # Mock model creation response
        model_response = Mock()
        model_response.status_code = 200
        model_response.json.return_value = {
            'status': 'success',
            'payload': {'id': 99, 'name': 'Dell Latitude 7420'}
        }

        # Mock hardware creation response
        hw_response = Mock()
        hw_response.status_code = 200
        hw_response.json.return_value = {
            'status': 'success',
            'payload': {'id': 100, 'asset_tag': 'TAG001'}
        }

        mock_retry.side_effect = [model_response, mock_retry.return_value, hw_response]

        status_code, result = create_hardware(
            asset_tag='TAG001',
            status_name='ACTIVE',
            model_name='Dell Latitude 7420',
            macAddress='a81d166742f7',
            createdDate='2024-01-15'
        )

        # Verify Gemini was called for categorization
        mock_gemini.gemini_prompt.assert_called_once()


class TestHardwareUpdateWorkflow(unittest.TestCase):
    """Tests for hardware update workflow."""

    @patch('snipe_it.retry_request')
    def test_update_hardware_success(self, mock_retry):
        """Test successfully updating existing hardware."""
        # Mock search response
        search_response = Mock()
        search_response.status_code = 200
        search_response.json.return_value = {
            'rows': [{'id': 100, 'asset_tag': 'TAG001', 'serial': 'SN001'}]
        }

        # Mock update response
        update_response = Mock()
        update_response.status_code = 200
        update_response.json.return_value = {'status': 'success'}

        mock_retry.side_effect = [search_response, update_response]

        update_hardware(
            asset_tag='TAG001',
            model_id=42,
            status_id=2,
            macAddress='a81d166742f7',
            createdDate='2024-01-15',
            ipAddress='192.168.1.100'
        )

        # Verify both search and update calls were made
        self.assertEqual(mock_retry.call_count, 2)

    @patch('snipe_it.retry_request')
    def test_update_hardware_not_found(self, mock_retry):
        """Test updating hardware when asset not found."""
        # Mock search response with no results
        search_response = Mock()
        search_response.status_code = 200
        search_response.json.return_value = {'rows': []}

        mock_retry.return_value = search_response

        update_hardware(
            asset_tag='NONEXISTENT',
            model_id=42,
            status_id=2
        )

        # Only search should be called
        mock_retry.assert_called_once()

    @patch('snipe_it.retry_request')
    def test_update_hardware_formats_mac_address(self, mock_retry):
        """Test that MAC address is formatted during update."""
        search_response = Mock()
        search_response.status_code = 200
        search_response.json.return_value = {
            'rows': [{'id': 100, 'asset_tag': 'TAG001'}]
        }

        update_response = Mock()
        update_response.status_code = 200
        update_response.json.return_value = {'status': 'success'}

        mock_retry.side_effect = [search_response, update_response]

        update_hardware(
            asset_tag='TAG001',
            model_id=42,
            status_id=2,
            macAddress='a81d166742f7'  # Raw format
        )

        # Verify the update payload contains formatted MAC
        update_call = mock_retry.call_args_list[1]
        update_payload = update_call[1]['json']
        self.assertIn('_snipeit_mac_address_1', update_payload)
        self.assertEqual(update_payload['_snipeit_mac_address_1'], 'a8:1d:16:67:42:f7')


class TestDeviceSyncWorkflow(unittest.TestCase):
    """Tests for complete device sync workflow."""

    @patch('snipe_it.googleAuth')
    @patch('snipe_it.create_hardware')
    def test_sync_multiple_devices(self, mock_create, mock_google_auth):
        """Test syncing multiple devices from Google."""
        # Mock Google device data
        mock_google_auth.fetch_and_print_chromeos_devices.return_value = [
            {
                'Serial Number': 'SN001',
                'Status': 'ACTIVE',
                'Model': 'Dell Chromebook 11',
                'Mac Address': 'a8:1d:16:67:42:f7',
                'Device User': 'user1@example.com',
                'Last Known IP Address': '192.168.1.100',
                'Active Time Ranges': [{'date': '2024-01-15'}],
                'EOL': '2025-06-15'
            },
            {
                'Serial Number': 'SN002',
                'Status': 'ACTIVE',
                'Model': 'ASUS Chromebook',
                'Mac Address': 'b8:2d:26:68:52:f8',
                'Device User': 'user2@example.com',
                'Last Known IP Address': '192.168.1.101',
                'Active Time Ranges': [{'date': '2024-01-14'}],
                'EOL': '2025-07-15'
            }
        ]

        mock_create.return_value = (200, {'status': 'success'})

        # Simulate main script loop
        devicedata = mock_google_auth.fetch_and_print_chromeos_devices()
        for device in devicedata:
            create_hardware(
                asset_tag=device['Serial Number'],
                status_name=device['Status'],
                model_name=device['Model'],
                macAddress=device['Mac Address'],
                createdDate=device['Active Time Ranges'][0]['date'],
                userEmail=device['Device User'],
                ipAddress=device['Last Known IP Address'],
                eol=device['EOL']
            )

        # Verify create_hardware was called for each device
        self.assertEqual(mock_create.call_count, 2)

    @patch('snipe_it.googleAuth')
    @patch('snipe_it.create_hardware')
    def test_sync_handles_missing_fields(self, mock_create, mock_google_auth):
        """Test device sync handles devices with missing optional fields."""
        mock_google_auth.fetch_and_print_chromeos_devices.return_value = [
            {
                'Serial Number': 'SN001',
                'Status': 'ACTIVE',
                'Model': 'Chromebook',
                'Mac Address': None,
                'Device User': None,
                'Last Known IP Address': None,
                'Active Time Ranges': None,
                'EOL': None
            }
        ]

        mock_create.return_value = (200, {'status': 'success'})

        devicedata = mock_google_auth.fetch_and_print_chromeos_devices()
        for device in devicedata:
            try:
                active_time = device.get('Active Time Ranges')[0].get('date')
            except (TypeError, IndexError):
                active_time = None

            create_hardware(
                asset_tag=device['Serial Number'],
                status_name=device['Status'],
                model_name=device['Model'],
                macAddress=device['Mac Address'],
                createdDate=active_time,
                userEmail=device['Device User'],
                ipAddress=device['Last Known IP Address'],
                eol=device['EOL']
            )

        self.assertEqual(mock_create.call_count, 1)


class TestErrorHandling(unittest.TestCase):
    """Tests for error handling in workflows."""

    @patch('snipe_it.get_model_id')
    @patch('snipe_it.get_status_id')
    @patch('snipe_it.retry_request')
    def test_create_hardware_handles_api_error(self, mock_retry, mock_status_id, mock_model_id):
        """Test handling of API errors during hardware creation."""
        mock_status_id.return_value = 2
        mock_model_id.return_value = 42

        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_retry.return_value = mock_response

        status_code, result = create_hardware(
            asset_tag='TAG001',
            status_name='ACTIVE',
            model_name='Dell Latitude',
            macAddress='a81d166742f7',
            createdDate='2024-01-15'
        )

        self.assertEqual(status_code, 500)

    @patch('snipe_it.get_model_id')
    @patch('snipe_it.get_status_id')
    @patch('snipe_it.retry_request')
    def test_create_hardware_handles_invalid_json(self, mock_retry, mock_status_id, mock_model_id):
        """Test handling of invalid JSON in API response."""
        mock_status_id.return_value = 2
        mock_model_id.return_value = 42

        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError('Invalid JSON')
        mock_response.text = 'Invalid JSON response'
        mock_retry.return_value = mock_response

        status_code, result = create_hardware(
            asset_tag='TAG001',
            status_name='ACTIVE',
            model_name='Dell Latitude',
            macAddress='a81d166742f7',
            createdDate='2024-01-15'
        )

        self.assertEqual(status_code, 200)
        self.assertEqual(result, 'Invalid JSON response')

    @patch('snipe_it.get_model_id')
    @patch('snipe_it.get_status_id')
    def test_create_hardware_handles_status_lookup_failure(self, mock_status_id, mock_model_id):
        """Test handling when status lookup fails."""
        mock_status_id.side_effect = Exception('Status lookup failed')
        mock_model_id.return_value = 42

        with patch('snipe_it.retry_request') as mock_retry:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'status': 'success'}
            mock_retry.return_value = mock_response

            # Should fall back to default status
            status_code, result = create_hardware(
                asset_tag='TAG001',
                status_name='UNKNOWN_STATUS',
                model_name='Dell Latitude',
                macAddress='a81d166742f7',
                createdDate='2024-01-15'
            )

            self.assertEqual(status_code, 200)


class TestDataValidation(unittest.TestCase):
    """Tests for data validation and sanitization."""

    def test_mac_address_formatting_in_workflow(self):
        """Test MAC address formatting is applied consistently."""
        test_cases = [
            ('a81d166742f7', 'a8:1d:16:67:42:f7'),
            ('a8:1d:16:67:42:f7', 'a8:1d:16:67:42:f7'),
            ('A81D166742F7', 'a8:1d:16:67:42:f7'),
            (None, None),
            ('', ''),
        ]

        for input_mac, expected_output in test_cases:
            result = format_mac(input_mac)
            self.assertEqual(result, expected_output,
                           f"Failed for input: {input_mac}")

    @patch('snipe_it.get_model_id')
    @patch('snipe_it.get_status_id')
    @patch('snipe_it.retry_request')
    def test_payload_construction_includes_all_fields(self, mock_retry, mock_status_id, mock_model_id):
        """Test that hardware payload includes all expected fields."""
        mock_status_id.return_value = 2
        mock_model_id.return_value = 42

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success'}
        mock_retry.return_value = mock_response

        create_hardware(
            asset_tag='TAG001',
            status_name='ACTIVE',
            model_name='Dell Latitude',
            macAddress='a81d166742f7',
            createdDate='2024-01-15',
            userEmail='user@example.com',
            ipAddress='192.168.1.100',
            eol='2025-06-15'
        )

        # Verify payload structure
        call_args = mock_retry.call_args_list[-1]
        payload = call_args[1]['json']

        self.assertIn('asset_tag', payload)
        self.assertIn('model_id', payload)
        self.assertIn('status_id', payload)
        self.assertIn('_snipeit_mac_address_1', payload)
        self.assertIn('_snipeit_sync_date_9', payload)
        self.assertIn('_snipeit_ip_address_3', payload)
        self.assertIn('_snipeit_user_10', payload)


if __name__ == '__main__':
    unittest.main()
