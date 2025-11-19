# Google2Snipe-IT Test Suite

Comprehensive test suite for the Google2Snipe-IT automation tool, including unit tests, integration tests, and CLI tests.

## Test Files

### 1. **test_format_mac.py**
Tests for MAC address formatting utility function.

**Coverage:**
- Basic MAC address formatting (raw 12-char to colon-separated)
- Handling already-formatted MACs
- None value handling
- Uppercase conversion
- Dash removal
- Whitespace stripping
- Invalid length handling

**Run:**
```bash
python -m pytest tests/test_format_mac.py -v
```

### 2. **test_snipeit.py**
Comprehensive unit tests for snipe-IT.py core functionality.

**Coverage:**
- `format_mac()` - MAC address formatting (expanded test cases)
- `retry_request()` - HTTP request retry logic with rate limiting
  - Successful requests on first try
  - 429 rate limit retries
  - Max retries exceeded
  - Request exception handling
  - Custom headers and JSON payloads
- `hardware_exists()` - Hardware existence checks
  - By asset tag
  - By serial number
  - Non-existent hardware
  - API error handling
- `get_model_id()` - Model ID lookups
  - Exact matches
  - Case-insensitive matching
  - Fallback to first result
  - Not found scenarios
  - API errors
- `get_status_id()` - Status ID lookups
- `get_category_id()` - Category ID lookups
- `get_user_id()` - User ID lookups by email
- `assign_fieldset_to_model()` - Fieldset assignment

**Run:**
```bash
python -m pytest tests/test_snipeit.py -v
python -m unittest tests.test_snipeit -v
```

### 3. **test_config.py**
Configuration module tests.

**Coverage:**
- **Validation Tests:**
  - Successful validation with all required variables
  - Missing API_TOKEN
  - Missing ENDPOINT_URL
  - Missing DELEGATED_ADMIN
  - Missing Google service account file
  - Missing Gemini API key
  - Multiple validation errors
- **Default Configuration:**
  - MAC address field default
  - Sync date field default
  - IP address field default
  - User field default
  - Model ID default (87)
  - Fieldset ID default (9)
  - Status ID default (2)
  - Log file default
  - Max retries default (4)
  - Retry delay default (20 seconds)
- **Custom Configuration:**
  - Field ID customization
  - DRY_RUN flag
  - DEBUG flag
  - ENVIRONMENT setting

**Run:**
```bash
python -m pytest tests/test_config.py -v
python -m unittest tests.test_config -v
```

### 4. **test_google_auth.py**
Google Workspace authentication and device retrieval tests.

**Coverage:**
- **Utility Functions:**
  - `bytes_to_gb()` - Byte to gigabyte conversion
- **Authentication:**
  - Successful authentication
  - File not found error handling
  - Generic exception handling
  - Scope inclusion
- **Device Fetching:**
  - Successful device list retrieval
  - Pagination handling
  - Empty results
  - Authentication failures
  - API errors
  - Missing field handling
  - Configuration respect (page size)
  - Field mapping completeness

**Run:**
```bash
python -m pytest tests/test_google_auth.py -v
python -m unittest tests.test_google_auth -v
```

### 5. **test_gemini.py**
AI-powered model categorization tests.

**Coverage:**
- **Gemini API Integration:**
  - Successful API calls
  - Response object handling
  - Category formatting with asterisks
  - Empty response handling
  - Long prompt handling
  - Various response format variations
  - Prompt pass-through
  - Model configuration
- **Module Initialization:**
  - API initialization
  - Multiple sequential calls

**Run:**
```bash
python -m pytest tests/test_gemini.py -v
python -m unittest tests.test_gemini -v
```

### 6. **test_integration.py**
End-to-end integration and workflow tests.

**Coverage:**
- **Hardware Creation Workflow:**
  - New hardware creation
  - Duplicate detection and update
  - New model creation with Gemini categorization
- **Hardware Update Workflow:**
  - Successful updates
  - Not found scenarios
  - MAC address formatting
- **Device Sync Workflow:**
  - Syncing multiple devices
  - Handling missing fields
- **Error Handling:**
  - API errors
  - Invalid JSON responses
  - Status lookup failures
- **Data Validation:**
  - MAC address formatting consistency
  - Payload construction completeness

**Run:**
```bash
python -m pytest tests/test_integration.py -v
python -m unittest tests.test_integration -v
```

## Running All Tests

### Using pytest (recommended)
```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=html

# Run specific test class
pytest tests/test_snipeit.py::TestFormatMac -v

# Run specific test method
pytest tests/test_snipeit.py::TestFormatMac::test_formats_plain_mac_address -v

# Run with specific markers
pytest tests/ -v -m unit
```

### Using unittest
```bash
# Run all tests
python -m unittest discover tests/ -v

# Run specific test module
python -m unittest tests.test_snipeit -v

# Run specific test class
python -m unittest tests.test_snipeit.TestFormatMac -v

# Run specific test method
python -m unittest tests.test_snipeit.TestFormatMac.test_formats_plain_mac_address -v
```

### Using the built-in test commands
```bash
# From the project root
python -m pytest tests/ -v

# Watch mode (requires pytest-watch)
ptw tests/
```

## Test Statistics

- **Total Test Files:** 6
- **Total Test Cases:** 100+
- **Coverage Areas:**
  - MAC address formatting: 8 tests
  - HTTP retry logic: 6 tests
  - Hardware management: 15+ tests
  - Model lookups: 6 tests
  - Status lookups: 3 tests
  - Category lookups: 2 tests
  - User lookups: 3 tests
  - Google Auth: 8 tests
  - Gemini API: 6 tests
  - Integration workflows: 15+ tests
  - Configuration validation: 15+ tests
  - Error handling: 5+ tests

## Mocking Strategy

Tests use Python's `unittest.mock` to mock external dependencies:

- **API Requests:** `mock.patch('snipe_it.retry_request')`
- **Google Services:** `mock.patch('googleAuth.build')`, `mock.patch('googleAuth.auth')`
- **Gemini API:** `mock.patch('gemini.genai.GenerativeModel')`
- **Environment Variables:** `mock.patch.dict(os.environ, ...)`
- **File System:** `mock.patch('os.path.exists')`

This ensures tests are fast, isolated, and don't depend on external services.

## Dependencies

Required for running tests:
```bash
pip install pytest pytest-cov pytest-watch
```

Or use the existing requirements.txt:
```bash
pip install -r requirements.txt
```

## Continuous Integration

Tests can be integrated with CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install pytest pytest-cov
    pytest tests/ --cov=. --cov-report=xml
```

## Test Development Guidelines

When adding new tests:

1. **Name tests descriptively:** `test_<function>_<scenario>`
2. **Use clear assertions:** Include failure messages
3. **Mock external dependencies:** Never make real API calls
4. **Test edge cases:** None values, empty lists, large inputs
5. **Isolate tests:** Each test should be independent
6. **Use fixtures for setup:** Avoid code duplication
7. **Document complex tests:** Add docstrings explaining intent

## Common Test Patterns

### Testing API Success
```python
@patch('snipe_it.retry_request')
def test_api_success(self, mock_retry):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'status': 'success'}
    mock_retry.return_value = mock_response

    result = some_function()
    self.assertEqual(result, expected)
```

### Testing Retries
```python
@patch('snipe_it.time.sleep')
@patch('snipe_it.requests.request')
def test_retries_on_rate_limit(self, mock_request, mock_sleep):
    mock_request.side_effect = [
        Mock(status_code=429),
        Mock(status_code=200)
    ]

    result = retry_request(...)
    self.assertEqual(mock_request.call_count, 2)
```

### Testing Error Handling
```python
@patch('snipe_it.retry_request')
def test_handles_error(self, mock_retry):
    mock_response = Mock()
    mock_response.status_code = 500
    mock_retry.return_value = mock_response

    result = some_function()
    self.assertIsNone(result)
```

## Troubleshooting

### Import Errors
If tests fail with import errors, ensure:
- All modules are in the Python path
- Dependencies are installed: `pip install -r requirements.txt`
- Environment variables are set in `.env`

### Mock Issues
If mocks aren't working:
- Check patch decorator path matches actual import
- Verify mock is applied before function call
- Use `mock.patch.object()` for module methods

### Test Isolation
If tests interfere with each other:
- Use `setUp()` and `tearDown()` for cleanup
- Reload modules if they cache state
- Reset mocks between tests with `mock.reset_mock()`

## Future Improvements

- [ ] Add pytest fixtures for common mock patterns
- [ ] Implement parameterized tests for multiple scenarios
- [ ] Add performance benchmarks
- [ ] Implement test data factories
- [ ] Add mutation testing
- [ ] Set up code coverage thresholds
- [ ] Add property-based testing with hypothesis
