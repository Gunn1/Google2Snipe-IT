import requests
import json
from dotenv import load_dotenv
import os
import googleAuth
import gemini
import time
from tqdm import tqdm
import logging

# Setup logging
logging.basicConfig(
    filename='snipeit_errors.log',
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# Load environment variables from .env file
load_dotenv()

# Access the variable
api_key = os.getenv("API_TOKEN") 
base_url = os.getenv("ENDPOINT_URL")

#No Model ID Default
default_model_id = 87



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
                tqdm.write(msg)
                logging.warning(msg)
                time.sleep(delay)
                continue
            return response
        except requests.RequestException as e:
            msg = f"Request error on {method} {url}: {e}"
            tqdm.write(msg)
            logging.error(msg)
            time.sleep(delay)
    
    msg = f"Max retries exceeded for {method} {url}"
    tqdm.write(msg)
    logging.error(msg)
    return None



def hardware_exists(asset_tag, serial, api_key, base_url=base_url):
    url = f"{base_url}/hardware"
    headers = {'Authorization': f'Bearer {api_key}', 'Accept': 'application/json'}
    params = {'search': asset_tag,
              'status': 'all' }
    
    response = retry_request("GET", url, headers=headers, params=params)


    if response.status_code == 200:
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
        tqdm.write(f"Failed to search for hardware: {response.status_code} - {response.text}")
        return

    devices = response.json().get("rows", [])
    matched_device = None
    for device in devices:
        if device.get("asset_tag") == asset_tag:
            matched_device = device
            break

    if not matched_device:
        tqdm.write(f"No matching device found for asset tag '{asset_tag}'")
        return

    # Build updated fields
    update_payload = {
        'model_id': model_id,
        'status_id': status_id,
        'asset_tag': asset_tag
    }

    # Add custom fields if present
    if macAddress:
        update_payload['_snipeit_mac_address_1'] = macAddress
    if createdDate:
        update_payload['_snipeit_sync_date_9'] = createdDate
    if ipAddress:
        update_payload['_snipeit_ip_address_3'] = ipAddress
    if last_User:
        update_payload['_snipeit_user_10'] = last_User
    if eol:
        print(f'EOL {eol}')
        update_payload['eol'] = eol

    hardware_id = matched_device['id']
    update_url = f"{base_url}/hardware/{hardware_id}"
    patch_headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    update_response = response = retry_request("PATCH", update_url, headers=patch_headers, json=update_payload)

    try:
        response_data = update_response.json()
    except ValueError:
        tqdm.write("Failed to parse JSON from Snipe-IT hardware response.")
        tqdm.write(f"Raw response: {response.text}")
        return response.status_code, response.text
    
    if update_response.status_code == 200 and response_data.get("status") == "success":
        tqdm.write(f"Updated hardware: {asset_tag}")
    else:
        tqdm.write(f"Failed to update hardware: {update_response.status_code} - {update_response.text}")


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

    if response.status_code == 200:
        tqdm.write(f"Fieldset successfully assigned to model {model_id}")
    else:
        tqdm.write(f"Failed to assign fieldset: {response.status_code}, {response.text}")

import time

def create_hardware(asset_tag, status_name, model_name, macAddress, createdDate, userEmail=None, ipAddress=None, eol=None):
    # if userEmail:
    #     userId = get_user_id(userEmail, api_key)
    # else:
    #     userId = None

    try:
        status_id = 2 if status_name == 'ACTIVE' else get_status_id(status_name, api_key)
    except Exception as e:
        tqdm.write(f"Status lookup failed: {e}")
        status_id = 5

    model_id = get_model_id(model_name, api_key)
    macAddress = format_mac(macAddress)
    if not model_id:
        tqdm.write(f"Model '{model_name}' not found. Creating new model...")
        if model_name is None:
            model_id = default_model_id
        else:
            category_name = gemini.gemini_prompt(f"""Given the following technology model,Model: {model_name} select the most appropriate category from this list:
iMac,Tablets,Mobile Devices,Servers,Networking Equipment,Printers & Scanners,Desktop,Chromebook
""").text  

            if '**' in category_name:
                category_name = category_name.split('**')[1].strip()
            else:
                tqdm.write(f"Warning: '**' not found in Gemini response. Full response: '{category_name}'")
                category_name = category_name.strip()

            category_id = get_category_id(category_name, api_key)
            model_data = {'name': model_name, 'category_id': category_id}
            url = f"{base_url}/models"
            headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
            model_response = retry_request("POST", url, headers=headers, json=model_data)


            try:
                response_data = model_response.json()
            except ValueError:
                tqdm.write("Failed to decode JSON from model creation response.")
                tqdm.write(f"Raw response: {model_response.text}")
                return

            if response_data.get("status") == "success":
                model_payload = response_data.get('payload', {})
                model_id = model_payload.get('id')
                tqdm.write(f"Model created successfully: {model_payload.get('name')}")
                assign_fieldset_to_model(model_id, fieldset_id=9, api_key=api_key)
            else:
                tqdm.write(f"Failed to create model: {response_data}")
                return

    # Construct the hardware payload
    hardware = {
        'asset_tag': asset_tag,
        'model_id': model_id,
        'status_id': status_id,
        'serial': asset_tag,
        '_snipeit_mac_address_1': macAddress,
        '_snipeit_sync_date_9': createdDate,
        '_snipeit_ip_address_3': ipAddress,
        '_snipeit_user_10': userEmail
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
        response = response = retry_request("POST", url, headers=headers, json=hardware)


        if response.status_code != 429:
            break

        tqdm.write(f"Rate limited (429). Attempt {attempt} of {max_attempts}. Waiting 10 seconds...")
        time.sleep(10)

    # Final result processing
    try:
        response_data = response.json()
    except ValueError:
        tqdm.write("Failed to parse JSON from Snipe-IT hardware response.")
        tqdm.write(f"Raw response: {response.text}")
        return response.status_code, response.text

    if response.status_code == 200 and response_data.get("status") == "success":
        return 200, response_data

    elif response_data.get("status") == "error":
        messages = response_data.get("messages", {})
        if "asset_tag" in messages or "serial" in messages:
            tqdm.write(f"Duplicate asset found for {asset_tag}. Updating instead.")
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
            tqdm.write(f"Error creating hardware: {response_data}")
            return 400, response_data

    else:
        tqdm.write(f"Unexpected response: {response.status_code} - {response.text}")
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
  from tqdm import tqdm

  url = f"{base_url}/models?search={name}"

  headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
  }

  try:
    response = retry_request("GET", url, headers=headers)

    if response.status_code == 200:
      data = json.loads(response.content)
      if data['rows']:
        # Try to match exact name (case-insensitive)
        for model in data['rows']:
          if model['name'].strip().lower() == name.strip().lower():
            return model['id']
        tqdm.write(f"No exact model match found for: {name}. Returning closest match.")
        return data['rows'][0]['id']  # Fallback if exact match not found
      else:
        tqdm.write(f"No model found with name: {name}")
        return None
    else:
      tqdm.write(f"API request failed with status code: {response.status_code}")
      tqdm.write(f"Response text: {response.text}")
      return None

  except requests.exceptions.RequestException as e:
    tqdm.write(f"An error occurred while making the API request: {e}")
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
            data = json.loads(response.content)
            # Extract the ID from the first matching status (assuming unique names)
            if data['rows']:
                return data['rows'][0]['id']
            else:
                tqdm.write(f"No status found with name: {name}")
                return None
        else:
            tqdm.write(f"API request failed with status code: {response.status_code}")
            tqdm.write(f"Response text: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        tqdm.write(f"An error occurred while making the API request: {e}")
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
        tqdm.write(f"No user found with email: {email}")
        return None 
    else:
      tqdm.write(f"API request failed with status code: {response.status_code}")
      tqdm.write(f"Response text: {response.text}")
      return None

  except requests.exceptions.RequestException as e:
    tqdm.write(f"An error occurred while making the API request: {e}")
    return None

def check_out_device(user):
    pass
def check_in_device():
    pass
def get_category_id(name: str, api_key: str, base_url: str = base_url):
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
                tqdm.write(f"No user found with email: {name}")
                return None 
        else:
            tqdm.write(f"API request failed with status code: {response.status_code}")
            tqdm.write(f"Response text: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        tqdm.write(f"An error occurred while making the API request: {e}")
        return None

if __name__ == '__main__':
    devicedata = googleAuth.fetch_and_print_chromeos_devices()
    total_devices = len(devicedata)
    tqdm.write(f"Found {total_devices} devices to process...\n")

    # Wrap loop with tqdm progress bar
    for idx, device in enumerate(tqdm(devicedata, desc="Processing Devices", unit="device"), start=1):
        try:
            active_time = device.get('Active Time Ranges')[0].get('date')
        except:
            logging.error("Active Time Not Set")
            active_time = None


        serial = device.get('Serial Number')
        status = device.get('Status')
        model = device.get('Model')
        mac = device.get('Mac Address')
        user = device.get('Device User')
        ip = device.get('Last Known IP Address')
        eol = device.get('EOL')

        status_code, result = create_hardware(serial, status, model, mac, active_time, user, ip, eol)

        # Optional: log errors if needed
        if status_code != 200:
            tqdm.write(f"\n[!] Error on {serial}: {result}")