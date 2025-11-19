import requests
import json
import logging
import time
from datetime import datetime
from tqdm import tqdm

import googleAuth
import gemini
from config import Config

# Note: Configuration validation happens in __main__ section for module import compatibility

# Setup logging with both file and console output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create convenience variables
api_key = Config.API_TOKEN
base_url = Config.ENDPOINT_URL
default_model_id = Config.SNIPE_IT_DEFAULT_MODEL_ID


class SyncStatistics:
    """Tracks sync statistics for reporting."""
    def __init__(self):
        self.total_devices = 0
        self.successful = 0
        self.failed = 0
        self.created = 0
        self.updated = 0
        self.start_time = None
        self.end_time = None

    def get_duration(self):
        """Returns sync duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0

    def print_summary(self):
        """Prints a formatted summary of sync statistics."""
        logger.info("=" * 70)
        logger.info("SYNC SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total devices processed: {self.total_devices}")
        logger.info(f"  ✓ Successful: {self.successful}")
        logger.info(f"  ✗ Failed: {self.failed}")
        logger.info(f"  → Created: {self.created}")
        logger.info(f"  ↻ Updated: {self.updated}")
        logger.info(f"Duration: {self.get_duration():.2f} seconds")
        logger.info("=" * 70)



def format_mac(mac: str) -> str:
    """
    Formats a MAC address string to colon-separated format (e.g., a81d166742f7 -> a8:1d:16:67:42:f7).
    Ignores formatting if input is None or already formatted.

    Args:
        mac (str): Raw MAC address string (12 hex characters).

    Returns:
        str: Formatted MAC address.
    """
    if not mac or ":" in mac:
        return mac  # Already formatted or None

    mac = mac.lower().replace("-", "").replace(":", "").strip()
    if len(mac) != 12:
        return mac  # Return as-is if not 12 chars

    return ":".join(mac[i:i+2] for i in range(0, 12, 2))

def retry_request(method, url, headers=None, json=None, params=None, retries=4, delay=20):
    for attempt in range(1, retries + 1):
        try:
            response = requests.request(method, url, headers=headers, json=json, params=params)
            if response.status_code == 429:
                msg = f"Rate limited on {url}. Attempt {attempt} of {retries}. Retrying in {delay} seconds..."
                logger.warning(msg)
                time.sleep(delay)
                continue
            return response
        except Exception as e:
            msg = f"Request error on {method} {url}: {e}"
            logger.error(msg)
            time.sleep(delay)

    msg = f"Max retries exceeded for {method} {url}"
    logger.error(msg)
    return None



def hardware_exists(asset_tag, serial, api_key, base_url=base_url):
    url = f"{base_url}/hardware"
    headers = {'Authorization': f'Bearer {api_key}', 'Accept': 'application/json'}
    params = {'search': asset_tag,
              'status': 'all' }
    
    response = retry_request("GET", url, headers=headers, params=params)

    if response and response.status_code == 200:
        for item in response.json().get('rows', []):
            if item.get('serial') == serial or item.get('asset_tag') == asset_tag:
                return True
    return False
def update_hardware(asset_tag, model_id, status_id, macAddress=None, createdDate=None, ipAddress=None, last_User=None,eol=None, api_key=api_key, base_url=base_url):
    """
    Updates an existing hardware asset in Snipe-IT using asset tag or serial.

    Args:
        asset_tag (str): The unique asset tag.
        model_id (int): ID of the model.
        status_id (int): Status ID to apply.
        macAddress (str, optional): MAC address custom field.
        createdDate (str, optional): Setup date (ISO format).
        ipAddress (str, optional): IP address custom field.
    """
    macAddress = format_mac(macAddress)

    # Search for hardware by asset tag
    url = f"{base_url}/hardware"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json'
    }
    params = {'search': asset_tag}
    response = retry_request("GET", url, headers=headers, params=params)

    if response.status_code != 200:
        logger.error(f"Failed to search for hardware: {response.status_code} - {response.text}")
        return

    devices = response.json().get("rows", [])
    matched_device = None
    for device in devices:
        if device.get("asset_tag") == asset_tag:
            matched_device = device
            break

    if not matched_device:
        logger.debug(f"No matching device found for asset tag '{asset_tag}'")
        return

    # Build updated fields
    update_payload = {
        'model_id': model_id,
        'status_id': status_id,
        'asset_tag': asset_tag
    }

    # Add custom fields if present
    if macAddress:
        update_payload[Config.SNIPE_IT_FIELD_MAC_ADDRESS] = macAddress
    if createdDate:
        update_payload[Config.SNIPE_IT_FIELD_SYNC_DATE] = createdDate
    if ipAddress:
        update_payload[Config.SNIPE_IT_FIELD_IP_ADDRESS] = ipAddress
    if last_User:
        update_payload[Config.SNIPE_IT_FIELD_USER] = last_User
    if eol:
        logger.debug(f'EOL {eol}')
        update_payload['eol'] = eol

    hardware_id = matched_device['id']
    update_url = f"{base_url}/hardware/{hardware_id}"
    patch_headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    update_response = retry_request("PATCH", update_url, headers=patch_headers, json=update_payload)

    try:
        response_data = update_response.json()
    except ValueError:
        logger.error("Failed to parse JSON from Snipe-IT hardware response.")
        logger.error(f"Raw response: {update_response.text}")
        return update_response.status_code, update_response.text

    if update_response.status_code == 200 and response_data.get("status") == "success":
        logger.info(f"Updated hardware: {asset_tag}")
    else:
        logger.error(f"Failed to update hardware: {update_response.status_code} - {update_response.text}")


def assign_fieldset_to_model(model_id, fieldset_id, api_key, base_url=base_url):
    """
    Assigns a fieldset to a model in Snipe-IT.

    Args:
        model_id (int): The model ID.
        fieldset_id (int): The ID of the fieldset (e.g., 'device' fieldset).
        api_key (str): API key for authentication.
        base_url (str): Base URL for your Snipe-IT instance.
    """
    url = f"{base_url}/models/{model_id}"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    data = {
        'fieldset_id': fieldset_id
    }
    response = retry_request("PATCH", url, headers=headers, json=data)

    if response and response.status_code == 200:
        logger.info(f"Fieldset successfully assigned to model {model_id}")
    else:
        logger.error(f"Failed to assign fieldset: {response.status_code if response else 'No response'}, {response.text if response else 'Connection failed'}")

import time

def create_hardware(asset_tag, status_name, model_name, macAddress, createdDate, userEmail=None, ipAddress=None, eol=None):
    # if userEmail:
    #     userId = get_user_id(userEmail, api_key)
    # else:
    #     userId = None

    try:
        if status_name == Config.SNIPE_IT_ACTIVE_STATUS:
            status_id = Config.SNIPE_IT_DEFAULT_STATUS_ID
        else:
            status_id = get_status_id(status_name, api_key)
            # Fallback to default if status not found
            if status_id is None:
                logger.debug(f"Status '{status_name}' not found in Snipe-IT. Using default status.")
                status_id = Config.SNIPE_IT_DEFAULT_STATUS_ID
    except Exception as e:
        logger.error(f"Status lookup error for status_name '{status_name}': {e}")
        status_id = Config.SNIPE_IT_DEFAULT_STATUS_ID

    model_id = get_model_id(model_name, api_key)
    macAddress = format_mac(macAddress)
    if not model_id:
        logger.info(f"Model '{model_name}' not found. Creating new model...")
        if model_name is None:
            model_id = default_model_id
        else:
            category_name = gemini.gemini_prompt(f"""Given the following technology model, Model: {model_name} select the most appropriate category from this list:
{Config.GEMINI_CATEGORIES}
""").text  

            if '**' in category_name:
                category_name = category_name.split('**')[1].strip()
            else:
                logger.warning(f"'**' not found in Gemini response. Full response: '{category_name}'")
                category_name = category_name.strip()

            category_id = get_category_id(category_name, api_key)
            model_data = {'name': model_name, 'category_id': category_id}
            url = f"{base_url}/models"
            headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
            model_response = retry_request("POST", url, headers=headers, json=model_data)


            try:
                response_data = model_response.json()
            except ValueError:
                logger.error("Failed to decode JSON from model creation response.")
                logger.error(f"Raw response: {model_response.text}")
                return

            if response_data.get("status") == "success":
                model_payload = response_data.get('payload', {})
                model_id = model_payload.get('id')
                logger.info(f"Model created successfully: {model_payload.get('name')}")
                assign_fieldset_to_model(model_id, fieldset_id=Config.SNIPE_IT_FIELDSET_ID, api_key=api_key)
            else:
                logger.error(f"Failed to create model: {response_data}")
                return

    # Construct the hardware payload
    hardware = {
        'asset_tag': asset_tag,
        'model_id': model_id,
        'status_id': status_id,
        'serial': asset_tag,
        Config.SNIPE_IT_FIELD_MAC_ADDRESS: macAddress,
        Config.SNIPE_IT_FIELD_SYNC_DATE: createdDate,
        Config.SNIPE_IT_FIELD_IP_ADDRESS: ipAddress,
        Config.SNIPE_IT_FIELD_USER: userEmail
    }

    url = f"{base_url}/hardware"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        "accept": "application/json"
    }


    # Retry logic
    max_attempts = 4
    for attempt in range(1, max_attempts + 1):
        response = retry_request("POST", url, headers=headers, json=hardware)


        if response.status_code != 429:
            break

        logger.warning(f"Rate limited (429). Attempt {attempt} of {max_attempts}. Waiting 10 seconds...")
        time.sleep(10)

    # Final result processing
    try:
        response_data = response.json()
    except ValueError:
        logger.error("Failed to parse JSON from Snipe-IT hardware response.")
        logger.error(f"Raw response: {response.text}")
        return response.status_code, response.text

    if response.status_code == 200 and response_data.get("status") == "success":
        return 200, response_data

    elif response_data.get("status") == "error":
        messages = response_data.get("messages", {})
        if "asset_tag" in messages or "serial" in messages:
            logger.info(f"Duplicate asset found for {asset_tag}. Updating instead.")
            update_hardware(
                asset_tag=asset_tag,
                model_id=model_id,
                status_id=status_id,
                macAddress=macAddress,
                createdDate=createdDate,
                ipAddress=ipAddress,
                last_User=userEmail,
                eol=eol
            )
            return 200, "Updated existing asset."
        else:
            logger.error(f"Error creating hardware: {response_data}")
            return 400, response_data

    else:
        logger.error(f"Unexpected response: {response.status_code} - {response.text}")
        return response.status_code, response.text

def get_model_id(name: str, api_key: str, base_url: str = base_url):
  """
  Retrieves the ID of a model in Snipe-IT using the provided name and API key.

  Args:
      name (str): The exact name of the model to search for.
      api_key (str): Your Snipe-IT API key.
      base_url (str, optional): The base URL of your Snipe-IT instance.

  Returns:
      int: The ID of the model if found, otherwise None.
  """

  import requests
  import json

  # Handle None input early
  if name is None:
    logger.debug("Model name is None. Returning None.")
    return None

  url = f"{base_url}/models?search={name}"

  headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
  }

  try:
    response = retry_request("GET", url, headers=headers)

    if response.status_code == 200:
      data = response.json()
      if data['rows']:
        # Try to match exact name (case-insensitive)
        for model in data['rows']:
          if model['name'].strip().lower() == name.strip().lower():
            return model['id']
        logger.debug(f"No exact model match found for: {name}. Returning closest match.")
        return data['rows'][0]['id']  # Fallback if exact match not found
      else:
        logger.debug(f"No model found with name: {name}")
        return None
    else:
      logger.error(f"API request failed with status code: {response.status_code}")
      logger.error(f"Response text: {response.text}")
      return None

  except Exception as e:
    logger.error(f"An error occurred while making the API request: {e}")
    return None

def get_status_id(name: str, api_key: str, base_url: str = base_url):
    """
    Retrieves the ID of a status in Snipe-IT using the provided name and API key.

    Args:
        name (str): The name of the status to search for.
        api_key (str): Your Snipe-IT API key.
        base_url (str, optional): The base URL of your Snipe-IT instance. Defaults to "https://your-snipeit-url/api/v1".

    Returns:
        int: The ID of the status if found, otherwise None.
    """

    # Handle None input early
    if name is None:
        logger.debug("Status name is None. Using default status.")
        return None

    # Construct the API endpoint URL
    url = f"{base_url}/statuslabels"

    # Set headers with the API key
    headers = {'Authorization': f'Bearer {api_key}',
               'Content-Type': 'application/json'
               }

    # Prepare the query parameters
    params = {'name': name}

    try:
        # Send a GET request to the API endpoint
        response = retry_request("GET", url, headers=headers, params=params)


        # Check for successful response (200 OK)
        if response.status_code == 200:
            data = response.json()
            # Extract the ID from the first matching status (assuming unique names)
            if data['rows']:
                return data['rows'][0]['id']
            else:
                logger.debug(f"No status found with name: {name}. Using default status.")
                return None
        else:
            logger.error(f"API request failed with status code: {response.status_code}")
            logger.error(f"Response text: {response.text}")
            return None

    except Exception as e:
        logger.error(f"An error occurred while making the API request: {e}")
        return None
def get_user_id(email: str, api_key: str, base_url: str = base_url):
  """
  Retrieves the ID of a user in Snipe-IT using the provided email and API key.

  Args:
      email (str): The email address of the user.
      api_key (str): Your Snipe-IT API key.
      base_url (str, optional): The base URL of your Snipe-IT instance.
          Defaults to "https://your-snipeit-url/api/v1".

  Returns:
      int: The ID of the user if found, otherwise None.
  """
  try:
    url = f"{base_url}/users"
    headers = {'Authorization': f'Bearer {api_key}',
               'Content-Type': 'application/json'
               }
    params = {'email': email}
    response = retry_request("GET", url, headers=headers, params=params)


    if response.status_code == 200:
      data = response.json()
      if data['rows']:
        return data['rows'][0]['id']
      else:
        logger.debug(f"No user found with email: {email}")
        return None
    else:
      logger.error(f"API request failed with status code: {response.status_code}")
      logger.error(f"Response text: {response.text}")
      return None

  except Exception as e:
    logger.error(f"An error occurred while making the API request: {e}")
    return None

def check_out_device(user):
    pass
def check_in_device():
    pass
def get_category_id(name: str, api_key: str, base_url: str = base_url):
    """
    Retrieves the ID of a category in Snipe-IT using the provided name and API key.

    Args:
        name (str): The name of the category.
        api_key (str): Your Snipe-IT API key.
        base_url (str, optional): The base URL of your Snipe-IT instance.
            Defaults to "https://your-snipeit-url/api/v1".

    Returns:
        int: The ID of the category if found, otherwise None.
    """
    try:
        url = f"{base_url}/categories"
        headers = {'Authorization': f'Bearer {api_key}',
               'Content-Type': 'application/json'
               }
        params = {'name': name}
        response = retry_request("GET", url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            if data['rows']:
                return data['rows'][0]['id']
            else:
                logger.debug(f"No category found with name: {name}")
                return None
        else:
            logger.error(f"API request failed with status code: {response.status_code}")
            logger.error(f"Response text: {response.text}")
            return None

    except Exception as e:
        logger.error(f"An error occurred while making the API request: {e}")
        return None

if __name__ == '__main__':
    # Validate configuration before proceeding
    is_valid, errors = Config.validate()
    if not is_valid:
        for error in errors:
            print(f"Configuration Error: {error}")
        exit(1)

    stats = SyncStatistics()
    stats.start_time = datetime.now()

    try:
        logger.info("=" * 70)
        logger.info("Starting Google2Snipe-IT Sync")
        logger.info("=" * 70)

        devicedata = googleAuth.fetch_and_print_chromeos_devices()
        stats.total_devices = len(devicedata)
        logger.info(f"Found {stats.total_devices} devices to process")

        # Wrap loop with tqdm progress bar
        for idx, device in enumerate(tqdm(devicedata, desc="Processing Devices", unit="device"), start=1):
            try:
                active_time = device.get('Active Time Ranges')[0].get('date')
            except:
                logger.warning("Active Time Not Set")
                active_time = None

            serial = device.get('Serial Number')
            status = device.get('Status')
            model = device.get('Model')
            mac = device.get('Mac Address')
            user = device.get('Device User')
            ip = device.get('Last Known IP Address')
            eol = device.get('EOL')

            status_code, result = create_hardware(serial, status, model, mac, active_time, user, ip, eol)

            # Track statistics
            if status_code == 200:
                stats.successful += 1
                if isinstance(result, dict) and result.get('payload'):
                    # Check if it was an update or create based on response
                    if 'Updated existing' in str(result):
                        stats.updated += 1
                    else:
                        stats.created += 1
            else:
                stats.failed += 1
                logger.error(f"Error on {serial}: {result}")

    except Exception as e:
        logger.exception(f"Fatal error during sync: {e}")
        exit(1)
    finally:
        stats.end_time = datetime.now()
        stats.print_summary()