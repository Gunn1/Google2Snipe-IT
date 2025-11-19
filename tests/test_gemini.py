"""
Unit tests for gemini.py module.
Tests AI-powered model categorization functionality.
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestGeminiPrompt(unittest.TestCase):
    """Tests for Gemini API prompt functionality."""

    @patch('gemini.genai.GenerativeModel')
    def test_gemini_prompt_success(self, mock_model_class):
        """Test successful Gemini API call."""
        from gemini import gemini_prompt

        mock_response = MagicMock()
        mock_response.text = '**Chromebook**'

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        # Re-import to get the patched version
        import importlib
        import gemini as gemini_module
        importlib.reload(gemini_module)

        result = gemini_module.gemini_prompt('What category is this device?')

        self.assertEqual(result.text, '**Chromebook**')

    @patch('gemini.genai.GenerativeModel')
    def test_gemini_prompt_returns_response_object(self, mock_model_class):
        """Test that gemini_prompt returns the full response object."""
        from gemini import gemini_prompt

        mock_response = MagicMock()
        mock_response.text = 'Some response'
        mock_response.usage_metadata = {'prompt_tokens': 10, 'candidates_tokens': 5}

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        import importlib
        import gemini as gemini_module
        importlib.reload(gemini_module)

        result = gemini_module.gemini_prompt('Test prompt')

        # Should return the actual response object, not just text
        self.assertEqual(result, mock_response)

    @patch('gemini.genai.GenerativeModel')
    def test_gemini_prompt_with_category_formatting(self, mock_model_class):
        """Test Gemini prompt returns formatted category in asterisks."""
        from gemini import gemini_prompt

        mock_response = MagicMock()
        mock_response.text = 'The device is a **Laptop** category device.'

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        import importlib
        import gemini as gemini_module
        importlib.reload(gemini_module)

        result = gemini_module.gemini_prompt('Categorize this device')

        self.assertIn('**Laptop**', result.text)

    @patch('gemini.genai.GenerativeModel')
    def test_gemini_prompt_handles_empty_response(self, mock_model_class):
        """Test handling of empty or whitespace response."""
        from gemini import gemini_prompt

        mock_response = MagicMock()
        mock_response.text = ''

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        import importlib
        import gemini as gemini_module
        importlib.reload(gemini_module)

        result = gemini_module.gemini_prompt('Test prompt')

        self.assertEqual(result.text, '')

    @patch('gemini.genai.GenerativeModel')
    def test_gemini_prompt_with_long_prompt(self, mock_model_class):
        """Test Gemini prompt with a long input prompt."""
        from gemini import gemini_prompt

        mock_response = MagicMock()
        mock_response.text = '**Chromebook**'

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        import importlib
        import gemini as gemini_module
        importlib.reload(gemini_module)

        long_prompt = "Given the following technology model, Model: Dell Chromebook 11 (3180) select the most appropriate category from this list: IMac,Tablets,Mobile Devices,Servers,Networking Equipment,Printers & Scanners,Desktop,Chromebook"

        result = gemini_module.gemini_prompt(long_prompt)

        mock_model.generate_content.assert_called_once_with(long_prompt)
        self.assertEqual(result.text, '**Chromebook**')

    @patch('gemini.genai.GenerativeModel')
    def test_gemini_prompt_various_category_formats(self, mock_model_class):
        """Test Gemini handling various response formats."""
        from gemini import gemini_prompt

        test_cases = [
            '**Desktop**',
            'The category is **Laptop**.',
            '**Mobile Devices** are the best fit.',
            'I recommend **Tablets** for this device.',
        ]

        for test_response in test_cases:
            mock_response = MagicMock()
            mock_response.text = test_response

            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_response
            mock_model_class.return_value = mock_model

            import importlib
            import gemini as gemini_module
            importlib.reload(gemini_module)

            result = gemini_module.gemini_prompt('Test')

            self.assertEqual(result.text, test_response)

    @patch('gemini.genai.GenerativeModel')
    def test_gemini_prompt_passes_prompt_to_model(self, mock_model_class):
        """Test that prompt is correctly passed to the model."""
        from gemini import gemini_prompt

        mock_response = MagicMock()
        mock_response.text = '**Category**'

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        import importlib
        import gemini as gemini_module
        importlib.reload(gemini_module)

        test_prompt = 'Custom prompt for categorization'
        gemini_module.gemini_prompt(test_prompt)

        mock_model.generate_content.assert_called_once_with(test_prompt)

    @patch('gemini.genai.GenerativeModel')
    def test_gemini_prompt_uses_configured_model(self, mock_model_class):
        """Test that Gemini uses the configured model."""
        from gemini import gemini_prompt

        mock_response = MagicMock()
        mock_response.text = '**Category**'

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        import importlib
        import gemini as gemini_module
        importlib.reload(gemini_module)

        gemini_module.gemini_prompt('Test')

        # Verify GenerativeModel was called with a model name
        mock_model_class.assert_called()


class TestGeminiIntegration(unittest.TestCase):
    """Integration tests for Gemini module."""

    @patch('gemini.genai.configure')
    @patch('gemini.genai.GenerativeModel')
    def test_gemini_initialization(self, mock_model_class, mock_configure):
        """Test Gemini API initialization."""
        import importlib
        import gemini as gemini_module

        # Reload to trigger initialization
        importlib.reload(gemini_module)

        # Verify configure was called
        mock_configure.assert_called_once()

        # Verify GenerativeModel was instantiated
        mock_model_class.assert_called_once()

    @patch('gemini.genai.GenerativeModel')
    def test_gemini_prompt_multiple_calls(self, mock_model_class):
        """Test multiple sequential Gemini prompts."""
        from gemini import gemini_prompt

        responses = [
            '**Chromebook**',
            '**Desktop**',
            '**Laptop**'
        ]

        for response_text in responses:
            mock_response = MagicMock()
            mock_response.text = response_text

            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_response
            mock_model_class.return_value = mock_model

            import importlib
            import gemini as gemini_module
            importlib.reload(gemini_module)

            result = gemini_module.gemini_prompt(f'Categorize device')

            self.assertEqual(result.text, response_text)


if __name__ == '__main__':
    unittest.main()
