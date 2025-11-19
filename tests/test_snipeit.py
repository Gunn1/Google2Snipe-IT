"""
Unit tests for snipe-IT.py module.
Tests core API functionality including hardware management, model operations, and retry logic.
"""

import unittest
import importlib.util
import sys
import types
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
import time

# Provide dummy modules for external dependencies so snipe-IT.py can be imported
for name in ['googleAuth', 'gemini']:
    if name not in sys.modules:
        sys.modules[name] = types.ModuleType(name)

# Dummy dotenv with load_dotenv function
if 'dotenv' not in sys.modules:
    dotenv_mod = types.ModuleType('dotenv')
    setattr(dotenv_mod, 'load_dotenv', lambda *args, **kwargs: None)
    sys.modules['dotenv'] = dotenv_mod

# Dummy tqdm - module-level functions
if 'tqdm' not in sys.modules:
    tqdm_mod = types.ModuleType('tqdm')
    setattr(tqdm_mod, 'tqdm', lambda *args, **kwargs: (x for x in args[0]) if args else [])
    setattr(tqdm_mod, 'write', lambda *args, **kwargs: None)
    sys.modules['tqdm'] = tqdm_mod

# Mock requests module with proper RequestException
if 'requests' not in sys.modules:
    class RequestException(Exception):
        pass

    requests_mod = types.ModuleType('requests')
    requests_mod.RequestException = RequestException
    sys.modules['requests'] = requests_mod

MODULE_PATH = Path(__file__).resolve().parents[1] / 'snipe-IT.py'
spec = importlib.util.spec_from_file_location('snipe_it', MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Store the module and import functions from it
snipe_it_module = module
sys.modules['snipe_it'] = snipe_it_module

# Import functions from loaded module
format_mac = module.format_mac
retry_request = module.retry_request
hardware_exists = module.hardware_exists
get_model_id = module.get_model_id
get_status_id = module.get_status_id
get_category_id = module.get_category_id
get_user_id = module.get_user_id
assign_fieldset_to_model = module.assign_fieldset_to_model


class TestFormatMac(unittest.TestCase):
    """Tests for MAC address formatting function."""

    def test_formats_plain_mac_address(self):
        """Test formatting raw 12-character MAC address."""
        result = format_mac('a81d166742f7')
        self.assertEqual(result, 'a8:1d:16:67:42:f7')

    def test_returns_already_formatted_mac(self):
        """Test that already formatted MAC addresses are returned unchanged."""
        mac = 'a8:1d:16:67:42:f7'
        result = format_mac(mac)
        self.assertEqual(result, mac)

    def test_returns_none_unchanged(self):
        """Test that None input returns None."""
        result = format_mac(None)
        self.assertIsNone(result)

    def test_handles_uppercase_mac(self):
        """Test formatting uppercase MAC addresses."""
        result = format_mac('A81D166742F7')
        self.assertEqual(result, 'a8:1d:16:67:42:f7')

    def test_strips_dashes_and_formats(self):
        """Test that dashes are stripped and MAC is formatted."""
        result = format_mac('a8-1d-16-67-42-f7')
        self.assertEqual(result, 'a8:1d:16:67:42:f7')

    def test_handles_whitespace(self):
        """Test MAC with leading/trailing whitespace."""
        result = format_mac('  a81d166742f7  ')
        self.assertEqual(result, 'a8:1d:16:67:42:f7')

    def test_returns_invalid_length_unchanged(self):
        """Test that invalid length MAC addresses are returned unchanged."""
        result = format_mac('a81d16')  # Too short
        self.assertEqual(result, 'a81d16')

    def test_empty_string_returned_unchanged(self):
        """Test empty string is returned unchanged."""
        result = format_mac('')
        self.assertEqual(result, '')


class TestRetryRequest(unittest.TestCase):
    """Tests for HTTP request retry logic with rate limiting."""

    @patch('snipe_it.requests.request')
    def test_successful_request_on_first_try(self, mock_request):
        """Test successful request returns immediately."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"status": "success"}'
        mock_request.return_value = mock_response

        result = retry_request('GET', 'http://test.com/api', retries=3, delay=1)

        self.assertEqual(result.status_code, 200)
        self.assertEqual(mock_request.call_count, 1)

    @patch('snipe_it.time.sleep')
    @patch('snipe_it.requests.request')
    def test_retries_on_rate_limit(self, mock_request, mock_sleep):
        """Test that 429 responses trigger retries."""
        rate_limited = Mock(status_code=429, text='Rate limited')
        success = Mock(status_code=200, text='Success')
        mock_request.side_effect = [rate_limited, success]

        result = retry_request('GET', 'http://test.com/api', retries=2, delay=1)

        self.assertEqual(result.status_code, 200)
        self.assertEqual(mock_request.call_count, 2)
        mock_sleep.assert_called_once_with(1)

    @patch('snipe_it.time.sleep')
    @patch('snipe_it.requests.request')
    def test_max_retries_exceeded(self, mock_request, mock_sleep):
        """Test that function returns None after max retries exceeded."""
        mock_response = Mock(status_code=429, text='Rate limited')
        mock_request.return_value = mock_response

        result = retry_request('GET', 'http://test.com/api', retries=2, delay=1)

        self.assertIsNone(result)
        self.assertEqual(mock_request.call_count, 2)
        # Should sleep after each attempt except the last
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('snipe_it.time.sleep')
    @patch('snipe_it.requests.request')
    def test_handles_request_exception(self, mock_request, mock_sleep):
        """Test handling of request exceptions."""
        mock_request.side_effect = [
            Exception('Connection error'),
            Mock(status_code=200, text='Success')
        ]

        result = retry_request('GET', 'http://test.com/api', retries=2, delay=1)

        self.assertEqual(result.status_code, 200)
        self.assertEqual(mock_request.call_count, 2)

    @patch('snipe_it.requests.request')
    def test_request_with_json_payload(self, mock_request):
        """Test request with JSON payload."""
        mock_response = Mock(status_code=200)
        mock_request.return_value = mock_response
        payload = {'key': 'value'}

        retry_request('POST', 'http://test.com/api', json=payload, retries=1)

        mock_request.assert_called_once_with(
            'POST', 'http://test.com/api',
            headers=None, json=payload, params=None
        )

    @patch('snipe_it.requests.request')
    def test_request_with_headers(self, mock_request):
        """Test request with custom headers."""
        mock_response = Mock(status_code=200)
        mock_request.return_value = mock_response
        headers = {'Authorization': 'Bearer token'}

        retry_request('GET', 'http://test.com/api', headers=headers, retries=1)

        mock_request.assert_called_once_with(
            'GET', 'http://test.com/api',
            headers=headers, json=None, params=None
        )


class TestHardwareExists(unittest.TestCase):
    """Tests for hardware existence check."""

    @patch('snipe_it.retry_request')
    def test_hardware_exists_by_asset_tag(self, mock_retry):
        """Test detecting existing hardware by asset tag."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'rows': [{'asset_tag': 'TAG001', 'serial': 'SN001'}]
        }
        mock_retry.return_value = mock_response

        result = hardware_exists('TAG001', 'SN001', 'test-key')

        self.assertTrue(result)

    @patch('snipe_it.retry_request')
    def test_hardware_exists_by_serial(self, mock_retry):
        """Test detecting existing hardware by serial number."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'rows': [{'asset_tag': 'TAG001', 'serial': 'SN001'}]
        }
        mock_retry.return_value = mock_response

        result = hardware_exists('TAG002', 'SN001', 'test-key')

        self.assertTrue(result)

    @patch('snipe_it.retry_request')
    def test_hardware_does_not_exist(self, mock_retry):
        """Test when hardware doesn't exist."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'rows': []}
        mock_retry.return_value = mock_response

        result = hardware_exists('TAG001', 'SN001', 'test-key')

        self.assertFalse(result)

    @patch('snipe_it.retry_request')
    def test_hardware_exists_api_error(self, mock_retry):
        """Test API error response."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_retry.return_value = mock_response

        result = hardware_exists('TAG001', 'SN001', 'test-key')

        self.assertFalse(result)


class TestGetModelId(unittest.TestCase):
    """Tests for model ID lookup."""

    @patch('snipe_it.retry_request')
    def test_get_model_id_exact_match(self, mock_retry):
        """Test retrieving model ID with exact name match."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'rows': [{'id': 42, 'name': 'Dell Latitude 7420'}]
        }
        mock_retry.return_value = mock_response

        result = get_model_id('Dell Latitude 7420', 'test-key')

        self.assertEqual(result, 42)

    @patch('snipe_it.retry_request')
    def test_get_model_id_case_insensitive(self, mock_retry):
        """Test case-insensitive model name matching."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'rows': [{'id': 42, 'name': 'Dell Latitude 7420'}]
        }
        mock_retry.return_value = mock_response

        result = get_model_id('dell latitude 7420', 'test-key')

        self.assertEqual(result, 42)

    @patch('snipe_it.retry_request')
    def test_get_model_id_fallback_to_first(self, mock_retry):
        """Test fallback to first result when exact match not found."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'rows': [
                {'id': 42, 'name': 'Dell Latitude 7420'},
                {'id': 43, 'name': 'Dell Latitude 7430'}
            ]
        }
        mock_retry.return_value = mock_response

        result = get_model_id('Different Model', 'test-key')

        self.assertEqual(result, 42)

    @patch('snipe_it.retry_request')
    def test_get_model_id_not_found(self, mock_retry):
        """Test when model is not found."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'rows': []}
        mock_retry.return_value = mock_response

        result = get_model_id('Nonexistent Model', 'test-key')

        self.assertIsNone(result)

    @patch('snipe_it.retry_request')
    def test_get_model_id_api_error(self, mock_retry):
        """Test handling API errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Server error'
        mock_retry.return_value = mock_response

        result = get_model_id('Dell Latitude', 'test-key')

        self.assertIsNone(result)


class TestGetStatusId(unittest.TestCase):
    """Tests for status ID lookup."""

    @patch('snipe_it.retry_request')
    def test_get_status_id_success(self, mock_retry):
        """Test retrieving status ID."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'rows': [{'id': 2, 'name': 'ACTIVE'}]
        }
        mock_retry.return_value = mock_response

        result = get_status_id('ACTIVE', 'test-key')

        self.assertEqual(result, 2)

    @patch('snipe_it.retry_request')
    def test_get_status_id_not_found(self, mock_retry):
        """Test when status is not found."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'rows': []}
        mock_retry.return_value = mock_response

        result = get_status_id('NONEXISTENT', 'test-key')

        self.assertIsNone(result)

    @patch('snipe_it.retry_request')
    def test_get_status_id_api_error(self, mock_retry):
        """Test API error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Server error'
        mock_retry.return_value = mock_response

        result = get_status_id('ACTIVE', 'test-key')

        self.assertIsNone(result)


class TestGetCategoryId(unittest.TestCase):
    """Tests for category ID lookup."""

    @patch('snipe_it.retry_request')
    def test_get_category_id_success(self, mock_retry):
        """Test retrieving category ID."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'rows': [{'id': 5, 'name': 'Laptops'}]
        }
        mock_retry.return_value = mock_response

        result = get_category_id('Laptops', 'test-key')

        self.assertEqual(result, 5)

    @patch('snipe_it.retry_request')
    def test_get_category_id_not_found(self, mock_retry):
        """Test when category is not found."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'rows': []}
        mock_retry.return_value = mock_response

        result = get_category_id('Nonexistent', 'test-key')

        self.assertIsNone(result)


class TestGetUserId(unittest.TestCase):
    """Tests for user ID lookup by email."""

    @patch('snipe_it.retry_request')
    def test_get_user_id_success(self, mock_retry):
        """Test retrieving user ID by email."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'rows': [{'id': 10, 'email': 'user@example.com'}]
        }
        mock_retry.return_value = mock_response

        result = get_user_id('user@example.com', 'test-key')

        self.assertEqual(result, 10)

    @patch('snipe_it.retry_request')
    def test_get_user_id_not_found(self, mock_retry):
        """Test when user is not found."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'rows': []}
        mock_retry.return_value = mock_response

        result = get_user_id('nonexistent@example.com', 'test-key')

        self.assertIsNone(result)

    @patch('snipe_it.retry_request')
    def test_get_user_id_api_error(self, mock_retry):
        """Test API error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Server error'
        mock_retry.return_value = mock_response

        result = get_user_id('user@example.com', 'test-key')

        self.assertIsNone(result)


class TestAssignFieldsetToModel(unittest.TestCase):
    """Tests for assigning fieldsets to models."""

    @patch('snipe_it.retry_request')
    def test_assign_fieldset_success(self, mock_retry):
        """Test successfully assigning fieldset to model."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_retry.return_value = mock_response

        # Should not raise an error
        assign_fieldset_to_model(42, 9, 'test-key')

        # Verify the correct endpoint was called
        call_args = mock_retry.call_args
        self.assertIn('/models/42', call_args[0][1])

    @patch('snipe_it.retry_request')
    def test_assign_fieldset_failure(self, mock_retry):
        """Test handling fieldset assignment failure."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Server error'
        mock_retry.return_value = mock_response

        # Should not raise an error, just log it
        assign_fieldset_to_model(42, 9, 'test-key')

        mock_retry.assert_called_once()


if __name__ == '__main__':
    unittest.main()
