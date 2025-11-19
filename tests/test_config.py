"""
Unit tests for config.py module.
Tests configuration validation, defaults, and environment variable handling.
"""

import unittest
import os
import sys
import types
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Mock dotenv before importing config
if 'dotenv' not in sys.modules:
    dotenv_mod = types.ModuleType('dotenv')
    setattr(dotenv_mod, 'load_dotenv', MagicMock())
    sys.modules['dotenv'] = dotenv_mod


class TestConfigValidation(unittest.TestCase):
    """Tests for configuration validation."""

    @patch.dict(os.environ, {
        'API_TOKEN': 'test-token',
        'ENDPOINT_URL': 'http://test.local/api/v1',
        'DELEGATED_ADMIN': 'admin@example.com',
        'Gemini_APIKEY': 'gemini-key',
        'GOOGLE_SERVICE_ACCOUNT_FILE': '/tmp/service_account.json'
    })
    @patch('config.os.path.exists')
    def test_validate_success_with_all_required_vars(self, mock_exists):
        """Test validation succeeds when all required variables are set."""
        mock_exists.return_value = True

        # Reimport config to pick up mocked environment
        import importlib
        import config
        importlib.reload(config)

        is_valid, errors = config.Config.validate()

        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    @patch.dict(os.environ, {}, clear=True)
    @patch('config.os.path.exists')
    def test_validate_fails_missing_api_token(self, mock_exists):
        """Test validation fails when API_TOKEN is missing."""
        mock_exists.return_value = True

        import importlib
        import config
        importlib.reload(config)

        is_valid, errors = config.Config.validate()

        self.assertFalse(is_valid)
        self.assertIn("API_TOKEN environment variable is required", errors)

    @patch.dict(os.environ, {
        'API_TOKEN': 'test-token',
        'DELEGATED_ADMIN': 'admin@example.com',
        'Gemini_APIKEY': 'gemini-key',
        'GOOGLE_SERVICE_ACCOUNT_FILE': '/tmp/service_account.json'
    }, clear=True)
    @patch('config.os.path.exists')
    def test_validate_fails_missing_endpoint_url(self, mock_exists):
        """Test validation fails when ENDPOINT_URL is missing."""
        mock_exists.return_value = True

        import importlib
        import config
        importlib.reload(config)

        is_valid, errors = config.Config.validate()

        self.assertFalse(is_valid)
        self.assertIn("ENDPOINT_URL environment variable is required", errors)

    @patch.dict(os.environ, {
        'API_TOKEN': 'test-token',
        'ENDPOINT_URL': 'http://test.local/api/v1',
        'Gemini_APIKEY': 'gemini-key',
        'GOOGLE_SERVICE_ACCOUNT_FILE': '/tmp/service_account.json'
    }, clear=True)
    @patch('config.os.path.exists')
    def test_validate_fails_missing_delegated_admin(self, mock_exists):
        """Test validation fails when DELEGATED_ADMIN is missing."""
        mock_exists.return_value = True

        import importlib
        import config
        importlib.reload(config)

        is_valid, errors = config.Config.validate()

        self.assertFalse(is_valid)
        self.assertIn("DELEGATED_ADMIN environment variable is required", errors)

    @patch.dict(os.environ, {
        'API_TOKEN': 'test-token',
        'ENDPOINT_URL': 'http://test.local/api/v1',
        'DELEGATED_ADMIN': 'admin@example.com',
        'Gemini_APIKEY': 'gemini-key'
    }, clear=True)
    @patch('config.os.path.exists')
    def test_validate_fails_missing_service_account_file(self, mock_exists):
        """Test validation fails when service account file doesn't exist."""
        mock_exists.return_value = False

        import importlib
        import config
        importlib.reload(config)

        is_valid, errors = config.Config.validate()

        self.assertFalse(is_valid)
        self.assertIn("Google service account file not found", errors[0])

    @patch.dict(os.environ, {
        'API_TOKEN': 'test-token',
        'ENDPOINT_URL': 'http://test.local/api/v1',
        'DELEGATED_ADMIN': 'admin@example.com',
        'GOOGLE_SERVICE_ACCOUNT_FILE': '/tmp/service_account.json'
    }, clear=True)
    @patch('config.os.path.exists')
    def test_validate_fails_missing_gemini_api_key(self, mock_exists):
        """Test validation fails when Gemini_APIKEY is missing."""
        mock_exists.return_value = True

        import importlib
        import config
        importlib.reload(config)

        is_valid, errors = config.Config.validate()

        self.assertFalse(is_valid)
        self.assertIn("Gemini_APIKEY environment variable is required", errors)

    @patch.dict(os.environ, {}, clear=True)
    @patch('config.os.path.exists')
    def test_validate_multiple_errors(self, mock_exists):
        """Test validation collects multiple errors."""
        mock_exists.return_value = False

        import importlib
        import config
        importlib.reload(config)

        is_valid, errors = config.Config.validate()

        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 1)


class TestConfigDefaults(unittest.TestCase):
    """Tests for configuration defaults."""

    @patch.dict(os.environ, {
        'API_TOKEN': 'test-token',
        'ENDPOINT_URL': 'http://test.local/api/v1',
        'DELEGATED_ADMIN': 'admin@example.com',
        'Gemini_APIKEY': 'gemini-key',
        'GOOGLE_SERVICE_ACCOUNT_FILE': '/tmp/service_account.json'
    }, clear=True)
    def test_default_mac_address_field(self):
        """Test default MAC address field ID."""
        import importlib
        import config
        importlib.reload(config)

        self.assertEqual(config.Config.SNIPE_IT_FIELD_MAC_ADDRESS, '_snipeit_mac_address_1')

    @patch.dict(os.environ, {
        'API_TOKEN': 'test-token',
        'ENDPOINT_URL': 'http://test.local/api/v1',
        'DELEGATED_ADMIN': 'admin@example.com',
        'Gemini_APIKEY': 'gemini-key',
        'GOOGLE_SERVICE_ACCOUNT_FILE': '/tmp/service_account.json'
    }, clear=True)
    def test_default_sync_date_field(self):
        """Test default sync date field ID."""
        import importlib
        import config
        importlib.reload(config)

        self.assertEqual(config.Config.SNIPE_IT_FIELD_SYNC_DATE, '_snipeit_sync_date_9')

    @patch.dict(os.environ, {
        'API_TOKEN': 'test-token',
        'ENDPOINT_URL': 'http://test.local/api/v1',
        'DELEGATED_ADMIN': 'admin@example.com',
        'Gemini_APIKEY': 'gemini-key',
        'GOOGLE_SERVICE_ACCOUNT_FILE': '/tmp/service_account.json'
    }, clear=True)
    def test_default_ip_address_field(self):
        """Test default IP address field ID."""
        import importlib
        import config
        importlib.reload(config)

        self.assertEqual(config.Config.SNIPE_IT_FIELD_IP_ADDRESS, '_snipeit_ip_address_3')

    @patch.dict(os.environ, {
        'API_TOKEN': 'test-token',
        'ENDPOINT_URL': 'http://test.local/api/v1',
        'DELEGATED_ADMIN': 'admin@example.com',
        'Gemini_APIKEY': 'gemini-key',
        'GOOGLE_SERVICE_ACCOUNT_FILE': '/tmp/service_account.json'
    }, clear=True)
    def test_default_user_field(self):
        """Test default user field ID."""
        import importlib
        import config
        importlib.reload(config)

        self.assertEqual(config.Config.SNIPE_IT_FIELD_USER, '_snipeit_user_10')

    @patch.dict(os.environ, {
        'API_TOKEN': 'test-token',
        'ENDPOINT_URL': 'http://test.local/api/v1',
        'DELEGATED_ADMIN': 'admin@example.com',
        'Gemini_APIKEY': 'gemini-key',
        'GOOGLE_SERVICE_ACCOUNT_FILE': '/tmp/service_account.json'
    }, clear=True)
    def test_default_model_id(self):
        """Test default model ID."""
        import importlib
        import config
        importlib.reload(config)

        self.assertEqual(config.Config.SNIPE_IT_DEFAULT_MODEL_ID, 87)

    @patch.dict(os.environ, {
        'API_TOKEN': 'test-token',
        'ENDPOINT_URL': 'http://test.local/api/v1',
        'DELEGATED_ADMIN': 'admin@example.com',
        'Gemini_APIKEY': 'gemini-key',
        'GOOGLE_SERVICE_ACCOUNT_FILE': '/tmp/service_account.json'
    }, clear=True)
    def test_default_fieldset_id(self):
        """Test default fieldset ID."""
        import importlib
        import config
        importlib.reload(config)

        self.assertEqual(config.Config.SNIPE_IT_FIELDSET_ID, 9)

    @patch.dict(os.environ, {
        'API_TOKEN': 'test-token',
        'ENDPOINT_URL': 'http://test.local/api/v1',
        'DELEGATED_ADMIN': 'admin@example.com',
        'Gemini_APIKEY': 'gemini-key',
        'GOOGLE_SERVICE_ACCOUNT_FILE': '/tmp/service_account.json'
    }, clear=True)
    def test_default_status_id(self):
        """Test default status ID."""
        import importlib
        import config
        importlib.reload(config)

        self.assertEqual(config.Config.SNIPE_IT_DEFAULT_STATUS_ID, 2)

    @patch.dict(os.environ, {
        'API_TOKEN': 'test-token',
        'ENDPOINT_URL': 'http://test.local/api/v1',
        'DELEGATED_ADMIN': 'admin@example.com',
        'Gemini_APIKEY': 'gemini-key',
        'GOOGLE_SERVICE_ACCOUNT_FILE': '/tmp/service_account.json'
    }, clear=True)
    def test_default_log_file(self):
        """Test default log file."""
        import importlib
        import config
        importlib.reload(config)

        self.assertEqual(config.Config.LOG_FILE, 'snipeit_errors.log')

    @patch.dict(os.environ, {
        'API_TOKEN': 'test-token',
        'ENDPOINT_URL': 'http://test.local/api/v1',
        'DELEGATED_ADMIN': 'admin@example.com',
        'Gemini_APIKEY': 'gemini-key',
        'GOOGLE_SERVICE_ACCOUNT_FILE': '/tmp/service_account.json'
    }, clear=True)
    def test_default_max_retries(self):
        """Test default max retries."""
        import importlib
        import config
        importlib.reload(config)

        self.assertEqual(config.Config.MAX_RETRIES, 4)

    @patch.dict(os.environ, {
        'API_TOKEN': 'test-token',
        'ENDPOINT_URL': 'http://test.local/api/v1',
        'DELEGATED_ADMIN': 'admin@example.com',
        'Gemini_APIKEY': 'gemini-key',
        'GOOGLE_SERVICE_ACCOUNT_FILE': '/tmp/service_account.json'
    }, clear=True)
    def test_default_retry_delay(self):
        """Test default retry delay."""
        import importlib
        import config
        importlib.reload(config)

        self.assertEqual(config.Config.RETRY_DELAY_SECONDS, 20)


class TestConfigCustomization(unittest.TestCase):
    """Tests for configuration customization via environment variables."""

    @patch.dict(os.environ, {
        'API_TOKEN': 'test-token',
        'ENDPOINT_URL': 'http://test.local/api/v1',
        'DELEGATED_ADMIN': 'admin@example.com',
        'Gemini_APIKEY': 'gemini-key',
        'GOOGLE_SERVICE_ACCOUNT_FILE': '/tmp/service_account.json',
        'SNIPE_IT_FIELD_MAC_ADDRESS': 'custom_mac_field',
        'SNIPE_IT_DEFAULT_MODEL_ID': '99',
        'MAX_RETRIES': '10'
    }, clear=True)
    def test_custom_field_ids(self):
        """Test customizing field IDs via environment variables."""
        import importlib
        import config
        importlib.reload(config)

        self.assertEqual(config.Config.SNIPE_IT_FIELD_MAC_ADDRESS, 'custom_mac_field')
        self.assertEqual(config.Config.SNIPE_IT_DEFAULT_MODEL_ID, 99)
        self.assertEqual(config.Config.MAX_RETRIES, 10)

    @patch.dict(os.environ, {
        'API_TOKEN': 'test-token',
        'ENDPOINT_URL': 'http://test.local/api/v1',
        'DELEGATED_ADMIN': 'admin@example.com',
        'Gemini_APIKEY': 'gemini-key',
        'GOOGLE_SERVICE_ACCOUNT_FILE': '/tmp/service_account.json',
        'DRY_RUN': 'true',
        'DEBUG': 'true'
    }, clear=True)
    def test_dry_run_and_debug_flags(self):
        """Test DRY_RUN and DEBUG flags."""
        import importlib
        import config
        importlib.reload(config)

        self.assertTrue(config.Config.DRY_RUN)
        self.assertTrue(config.Config.DEBUG)

    @patch.dict(os.environ, {
        'API_TOKEN': 'test-token',
        'ENDPOINT_URL': 'http://test.local/api/v1',
        'DELEGATED_ADMIN': 'admin@example.com',
        'Gemini_APIKEY': 'gemini-key',
        'GOOGLE_SERVICE_ACCOUNT_FILE': '/tmp/service_account.json',
        'ENVIRONMENT': 'production'
    }, clear=True)
    def test_environment_setting(self):
        """Test ENVIRONMENT setting."""
        import importlib
        import config
        importlib.reload(config)

        self.assertEqual(config.Config.ENVIRONMENT, 'production')


if __name__ == '__main__':
    unittest.main()
