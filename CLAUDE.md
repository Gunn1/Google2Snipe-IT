# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Google2Snipe-IT is a Python automation tool that syncs ChromeOS device data from Google Workspace (via Google Admin SDK) into a Snipe-IT asset inventory system. The tool handles authentication, device data transformation, model/category creation, and hardware asset management with automatic duplicate detection and rate-limit handling.

## Architecture

### Core Components

1. **snipe-IT.py** - Main orchestration module
   - Handles all Snipe-IT API interactions (CRUD operations on hardware, models, categories, statuses)
   - Implements retry logic with exponential backoff for rate-limited requests (HTTP 429)
   - Two main workflows:
     - `create_hardware()`: Creates new devices or updates duplicates via `hardware_exists()` check
     - `update_hardware()`: Patches existing assets with new data
   - Uses Gemini AI to auto-categorize models when creating new ones
   - Formats MAC addresses from raw hex strings to colon-separated notation
   - Custom field mapping for Snipe-IT (e.g., `_snipeit_mac_address_1`, `_snipeit_sync_date_9`)

2. **googleAuth.py** - Google Workspace authentication and data retrieval
   - Uses service account with domain-wide delegation for ChromeOS Admin API access
   - `fetch_and_print_chromeos_devices()`: Paginates through all ChromeOS devices, returns structured device data
   - Extracts fields: serial number, status, model, MAC address, IP, enrollment date, EOL date, last user email

3. **gemini.py** - AI-powered helper for model categorization
   - Wraps Google Gemini API to intelligently classify device models into predefined categories
   - Parses Gemini's markdown-formatted response (looks for category wrapped in `**`)

### Data Flow

```
Google Workspace (ChromeOS devices)
        ↓
googleAuth.fetch_and_print_chromeos_devices()
        ↓
Device data dict with keys: Device User, Serial Number, Status, Model, Mac Address, Last Known IP Address, EOL, Active Time Ranges
        ↓
snipe-IT.py main loop (processes with tqdm progress bar)
        ↓
For each device:
  1. Call create_hardware() with model name, serial, MAC, IP, user, status, EOL
  2. If duplicate detected → update_hardware() instead
  3. If model doesn't exist → gemini.gemini_prompt() determines category → create model in Snipe-IT
  4. Fieldset 9 auto-assigned to new models
  5. Custom fields populated in hardware payload
```

### Key Configuration IDs

These are hardcoded or referenced - check your Snipe-IT instance:
- **default_model_id = 87**: Fallback model when model_name is None
- **fieldset_id = 9**: Fieldset assigned to all newly created models
- **status_id = 2**: Default "ACTIVE" status
- **Custom fields**:
  - `_snipeit_mac_address_1`: MAC address field
  - `_snipeit_sync_date_9`: Setup/sync date
  - `_snipeit_ip_address_3`: IP address field
  - `_snipeit_user_10`: Device user email

### Environment Variables

Required in `.env`:
- `API_TOKEN`: Snipe-IT API key
- `ENDPOINT_URL`: Snipe-IT base URL (e.g., `https://your-instance/api/v1`)
- `DELEGATED_ADMIN`: Google Workspace admin email for domain-wide delegation
- `Gemini_APIKEY`: Google Gemini API key (for model categorization)

Required file:
- `service_account.json`: Google service account key with `admin.directory.device.chromeos` scope

## Common Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the full sync (fetches from Google, syncs to Snipe-IT)
python snipe-IT.py

# Run unit tests
python -m pytest tests/ -v
# or
python -m unittest tests.test_format_mac

# Run a single test
python -m unittest tests.test_format_mac.TestFormatMac.test_normalizes_plain_mac
```

## Key Functions and Their Signatures

**snipe-IT.py**
- `format_mac(mac: str) -> str`: Converts raw MAC strings to colon-separated (e.g., `a81d166742f7` → `a8:1d:16:67:42:f7`)
- `retry_request(method, url, headers=None, json=None, params=None, retries=4, delay=20)`: HTTP wrapper with 429 rate-limit backoff
- `hardware_exists(asset_tag, serial, api_key, base_url=base_url) -> bool`: Checks if asset exists
- `create_hardware(asset_tag, status_name, model_name, macAddress, createdDate, userEmail=None, ipAddress=None, eol=None) -> tuple`: Creates device or updates if duplicate
- `update_hardware(asset_tag, model_id, status_id, macAddress=None, createdDate=None, ipAddress=None, last_User=None, eol=None, api_key=api_key, base_url=base_url)`: Updates existing asset
- `get_model_id(name: str, api_key: str, base_url: str = base_url) -> int | None`: Looks up model ID by name
- `get_status_id(name: str, api_key: str, base_url: str = base_url) -> int | None`: Looks up status ID by name
- `get_category_id(name: str, api_key: str, base_url: str = base_url) -> int | None`: Looks up category ID by name
- `get_user_id(email: str, api_key: str, base_url: str = base_url) -> int | None`: Looks up user ID by email
- `assign_fieldset_to_model(model_id, fieldset_id, api_key, base_url=base_url)`: Associates fieldset with model

**googleAuth.py**
- `auth() -> google.auth.credentials.Credentials`: Authenticates using service account
- `fetch_and_print_chromeos_devices() -> list[dict]`: Returns all ChromeOS devices from Google Workspace

**gemini.py**
- `gemini_prompt(prompt: str) -> google.generativeai.types.GenerateContentResponse`: Calls Gemini API with prompt

## Testing Notes

- Tests use mocks/dummies for external dependencies (requests, googleAuth, gemini, tqdm, dotenv)
- Test file: `tests/test_format_mac.py` - covers MAC address formatting edge cases (None, already formatted, valid raw MAC)
- Currently limited test coverage; most business logic untested

## Logging

- Errors logged to `snipeit_errors.log` at WARNING level and above
- Progress and errors also written to terminal via `tqdm.write()`
- Failed requests log response status codes and raw response text

## Important Implementation Details

1. **Duplicate Detection**: `hardware_exists()` searches by asset_tag AND serial. `create_hardware()` catches duplicate asset_tag/serial errors from API response and calls `update_hardware()` automatically.

2. **Model Auto-Creation**: If model not found, Gemini AI categorizes it, creates the model, then assigns fieldset 9.

3. **Rate Limiting**: `retry_request()` respects HTTP 429 with configurable retry count (default 4) and delay (default 20 seconds).

4. **MAC Formatting**: Only normalizes if input is 12 hex chars without colons/dashes. Returns None unchanged, already-formatted MACs unchanged.

5. **Custom Fields**: Snipe-IT uses underscored field IDs (e.g., `_snipeit_mac_address_1`). Mapping is hardcoded in `create_hardware()` and `update_hardware()`.

6. **EOL Date**: Mapped from Google's `autoUpdateThrough` field. Assigned to Snipe-IT's `eol` field.

## Potential Improvements & Known Issues

- `check_out_device()` and `check_in_device()` are stubs - not implemented
- Hardcoded custom field IDs may differ across Snipe-IT instances (should be configurable)
- No pagination for Snipe-IT hardware search (assumes search results fit in one page)
- Gemini categorization assumes categories exist in Snipe-IT (no fallback creation)
- `print()` call on line 142 in snipe-IT.py should use `tqdm.write()` for consistency
