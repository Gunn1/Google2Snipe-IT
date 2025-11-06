# Google ChromeOS to Snipe-IT Sync

This script automates the process of syncing ChromeOS device data from the **Google Admin SDK** into your **Snipe-IT** asset inventory.

It fetches device data using a Google service account with domain-wide delegation and pushes it to Snipe-IT. Duplicate devices are automatically updated. All activity is logged and a progress bar shows sync status.

---

## 🔧 Features

* ✅ Authenticates using a **service account** with domain-wide delegation
* ✅ Fetches **all ChromeOS devices** with pagination support
* ✅ Parses and formats relevant fields (MAC, IP, model, enrollment date, etc.)
* ✅ Automatically creates **models and categories** using AI classification
* ✅ Assigns **fieldsets with custom fields** to new models
* ✅ Updates existing devices based on asset tag
* ✅ Handles **API rate limiting (429)** with exponential backoff retry logic
* ✅ Logs errors to file with configurable logging levels
* ✅ Displays live **progress bar** with `tqdm`
* ✅ **Development and Production deployment** modes
* ✅ **SystemD timer** for automated scheduled syncs
* ✅ **Centralized configuration** management via environment variables

---

## 📦 Requirements

* Python 3.8+
* [Snipe-IT](https://snipeitapp.com/) API access
* Google Workspace Admin access with service account + delegation
* Internet connectivity for Google Admin SDK and Snipe-IT API calls

### Python Dependencies

All dependencies are installed automatically by the setup script. See `requirements.txt` for details.

---

## ⚒️ Quick Start (Recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/Gunn1/Google2Snipe-IT.git
cd Google2Snipe-IT
```

### 2. Run the Setup Script

The interactive setup script handles everything for you:

```bash
chmod +x setup.sh
./setup.sh
```

This script will:
- ✅ Check Python version (3.8+)
- ✅ Create a Python virtual environment
- ✅ Install all dependencies
- ✅ Guide you through configuration (development or production)
- ✅ Create a `.env` file with your settings
- ✅ (Production only) Set up SystemD service and timer
- ✅ Validate your configuration

### 3. Place Your Google Service Account Key

Obtain your service account JSON key from [Google Cloud Console](https://console.cloud.google.com/):

1. Create a service account with **domain-wide delegation** enabled
2. Grant it the scope: `https://www.googleapis.com/auth/admin.directory.device.chromeos`
3. Download the JSON key
4. Save it as `service_account.json` in the project directory

---

## 📋 Manual Setup (Advanced)

If you prefer to set up manually instead of using the setup script:

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example configuration and customize it:

```bash
cp .env.example .env
```

Edit `.env` with your settings. See [Configuration](#configuration) section for details.

### 4. Place Service Account Key

Save your Google service account JSON as `service_account.json` in the project directory.

### 5. Run the Sync

```bash
python snipe-IT.py
```

---

## 🔧 Configuration

Configuration is managed via environment variables in the `.env` file. See `.env.example` for a complete example with documentation.

### Required Configuration

```env
# Snipe-IT
API_TOKEN=your_snipeit_api_key
ENDPOINT_URL=https://your-snipeit-instance/api/v1

# Google Workspace
DELEGATED_ADMIN=admin@your-domain.com
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json

# Gemini AI
Gemini_APIKEY=your_gemini_api_key
```

### Custom Field Mapping

Map Snipe-IT custom field IDs in your `.env`:

```env
SNIPE_IT_FIELD_MAC_ADDRESS=_snipeit_mac_address_1
SNIPE_IT_FIELD_SYNC_DATE=_snipeit_sync_date_9
SNIPE_IT_FIELD_IP_ADDRESS=_snipeit_ip_address_3
SNIPE_IT_FIELD_USER=_snipeit_user_10
```

Find your custom field IDs in Snipe-IT at: **Settings → Custom Fields**

### Optional Configuration

```env
# Defaults
SNIPE_IT_DEFAULT_MODEL_ID=87
SNIPE_IT_FIELDSET_ID=9
SNIPE_IT_DEFAULT_STATUS_ID=2

# Google API
GOOGLE_CHROMEOS_PAGE_SIZE=300
GOOGLE_CHROMEOS_PROJECTION=FULL

# Retry Logic
MAX_RETRIES=4
RETRY_DELAY_SECONDS=20

# Logging
LOG_FILE=snipeit_errors.log
LOG_LEVEL=WARNING

# Features
DEBUG=false
DRY_RUN=false
ENVIRONMENT=development
```

---

## ▶️ Running the Sync

### Development Mode

For testing and manual runs:

```bash
source venv/bin/activate
python snipe-IT.py
```

To test without making changes (dry-run):

```bash
export DRY_RUN=true
python snipe-IT.py
```

### Production Mode

After running `./setup.sh` and selecting production, the sync runs automatically via SystemD timer.

#### Manual Trigger

```bash
# Run the sync immediately
systemctl start google2snipeit.service

# Check status
systemctl status google2snipeit.service

# View recent logs
journalctl -u google2snipeit.service -n 50 -f
```

#### SystemD Timer Management

```bash
# Check timer status
systemctl status google2snipeit.timer

# View next scheduled run
systemctl list-timers google2snipeit.timer

# View all recent runs and logs
journalctl -u google2snipeit.service -n 100

# Follow logs in real-time
journalctl -u google2snipeit.service -f
```

#### Customizing the Schedule

Edit the SystemD timer to change the schedule:

```bash
sudo systemctl edit google2snipeit.timer
```

Common schedule patterns:

```ini
# Every 15 minutes
OnUnitActiveSec=15min

# Every 30 minutes
OnUnitActiveSec=30min

# Every hour
OnUnitActiveSec=1h

# Every 4 hours
OnUnitActiveSec=4h

# Daily at 2 AM
OnCalendar=*-*-* 02:00:00

# Weekdays at 9 AM
OnCalendar=Mon-Fri *-*-* 09:00:00
```

After editing:

```bash
sudo systemctl daemon-reload
sudo systemctl restart google2snipeit.timer
```

---

## 📊 Understanding the Sync Process

```
1. Authenticate with Google Workspace using service account
   ↓
2. Fetch all ChromeOS devices (with pagination)
   ↓
3. For each device:
   ├─ Format MAC address (e.g., a81d166742f7 → a8:1d:16:67:42:f7)
   ├─ Check if device exists in Snipe-IT (by asset tag or serial)
   │  ├─ If exists: Update with new data
   │  └─ If not: Create new device
   ├─ If model doesn't exist:
   │  ├─ Use Gemini AI to classify into a category
   │  ├─ Create model in Snipe-IT
   │  └─ Assign custom field fieldset
   └─ Log any errors
   ↓
4. Display progress and summary
```

---

## 🧠 Key Concepts

### Duplicate Detection

The sync checks if a device already exists by matching:
- Asset tag (serial number from ChromeOS)
- Serial number

If found, the existing device is **updated** with new data instead of creating a duplicate.

### MAC Address Normalization

Raw MAC addresses like `a81d166742f7` are automatically converted to the standard format `a8:1d:16:67:42:f7`.

### Model Auto-Creation

If a ChromeOS model doesn't exist in Snipe-IT:
1. Google Gemini AI classifies it into a category (Chromebook, Desktop, Tablet, etc.)
2. A new model is created with the category
3. The configured fieldset is assigned to the model

If Gemini classification fails, the default model is used.

### Custom Fields

Data is stored in Snipe-IT custom fields:
- **MAC Address**: Network adapter MAC address
- **Sync Date**: When the device was enrolled (from ChromeOS)
- **IP Address**: Last known IP address
- **User**: Email of the device's last user

---

## 📝 Logging

### Log File

Errors and warnings are logged to `snipeit_errors.log` (or custom path via `LOG_FILE` env var).

### Log Levels

Configure via `LOG_LEVEL` environment variable:
- `DEBUG`: Verbose output, all function calls
- `INFO`: Informational messages
- `WARNING`: Only warnings and errors (default)
- `ERROR`: Only errors
- `CRITICAL`: Only critical failures

### Real-Time Output

During sync, progress is displayed with:
- Live progress bar (total device count)
- Status messages for each operation
- Error messages for failed devices
- Summary statistics at completion

---

## 🔍 Troubleshooting

### Configuration Errors

If you see configuration errors on startup, check:

```bash
# Validate your setup
python3 -c "from config import Config; is_valid, errors = Config.validate(); print('Valid' if is_valid else f'Errors: {errors}')"
```

### Missing Dependencies

```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt
```

### Service Account Issues

```bash
# Check service account file exists
ls -la service_account.json

# Verify it's valid JSON
python3 -m json.tool service_account.json
```

### API Authentication Failures

- Verify `API_TOKEN` is a valid Snipe-IT API key
- Verify `ENDPOINT_URL` is correct (ends with `/api/v1`)
- Verify `DELEGATED_ADMIN` email has ChromeOS device access
- Verify Gemini API key is valid

### Rate Limiting (HTTP 429)

The script automatically retries with exponential backoff. If you still experience issues:
- Increase `MAX_RETRIES` in `.env`
- Increase `RETRY_DELAY_SECONDS` in `.env`
- Reduce `GOOGLE_CHROMEOS_PAGE_SIZE` to fetch fewer devices per request

### SystemD Timer Not Running

```bash
# Check if enabled
systemctl is-enabled google2snipeit.timer

# Enable if disabled
sudo systemctl enable google2snipeit.timer

# Check logs for errors
journalctl -u google2snipeit.service -p err

# Check timer status
systemctl status google2snipeit.timer
```

### No Custom Fields Appearing in Snipe-IT

1. Verify custom field IDs in `.env` match your Snipe-IT instance
2. Verify the fieldset contains those custom fields
3. Verify `SNIPE_IT_FIELDSET_ID` is assigned to the model

To find correct field IDs:
1. In Snipe-IT, go to **Settings → Custom Fields**
2. Click on a field to see its ID (e.g., `_snipeit_mac_address_1`)
3. Update your `.env` file

---

## 🔒 Security Considerations

### Environment Variables & Secrets

⚠️ **IMPORTANT**: The `.env` file contains API keys and tokens.

- **Never commit `.env` to version control** (it's in `.gitignore`)
- **Restrict file permissions**: `chmod 600 .env`
- **Rotate API keys periodically**
- **Use strong, unique API keys**

### Production Deployment

When deploying to production:

1. Run `setup.sh` with production mode selected
2. Ensure the service account has **minimal required permissions**
3. Use a dedicated service account user (`_google2snipeit`) created automatically
4. Monitor logs regularly: `journalctl -u google2snipeit.service -f`
5. Set up log rotation for `snipeit_errors.log` to prevent disk fill
6. Consider running behind a proxy or VPN if your Snipe-IT is internal

### Snipe-IT API Token Security

- Create a dedicated Snipe-IT admin account for this service
- Use the smallest permission set needed (asset creation/update)
- Regularly rotate the API token
- Monitor failed API authentication attempts in logs

---

## 📊 Recent Changes

### Version 2.0 (Current)

**New Features:**
- ✨ Centralized configuration management via `config.py`
- ✨ Interactive setup script (`setup.sh`) for easy deployment
- ✨ Production-ready SystemD service and timer
- ✨ Support for dev and production environments
- ✨ Enhanced logging with configurable levels
- ✨ Configuration validation at startup
- ✨ Comprehensive documentation

**Improvements:**
- 🔧 Replaced hardcoded values with environment variables
- 🔧 Better error handling and logging
- 🔧 Virtual environment support
- 🔧 Dry-run mode for testing
- 🔧 Debug logging for troubleshooting

**Breaking Changes:**
- Configuration now uses `config.py` - existing `.env` files should still work
- Some hardcoded field IDs now require environment variables (see `.env.example`)

### Version 1.0 (Original)

- Basic ChromeOS to Snipe-IT sync
- Service account authentication
- Duplicate detection and update
- Basic error logging

---

## 🧪 Testing

To test the sync without making changes:

```bash
# Activate virtual environment
source venv/bin/activate

# Run in dry-run mode
export DRY_RUN=true
python snipe-IT.py

# View what would have been changed (check logs)
tail -f snipeit_errors.log
```

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

Contributions are welcome! Please feel free to open issues or PRs for:
- Bug fixes
- New features
- Documentation improvements
- Additional Snipe-IT field support
- Performance optimizations

Before submitting a PR, please:
1. Test your changes with `python -m pytest tests/`
2. Ensure no sensitive data is committed
3. Update documentation if needed

---

## 📞 Support

For issues, questions, or suggestions:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review logs: `tail -f snipeit_errors.log`
3. Open a GitHub issue with:
   - Description of the problem
   - Relevant log excerpts (no API keys!)
   - Your configuration (no API keys!)
   - Python version: `python3 --version`
