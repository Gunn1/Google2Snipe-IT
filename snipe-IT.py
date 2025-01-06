import requests
import json
from dotenv import load_dotenv
import os
import googleAuth
# Load environment variables from .env file
load_dotenv()

# Access the variable
api_key = os.getenv("API_TOKEN") 
base_url = os.getenv("ENDPOINT_URL")



def create_hardware(asset_tag, status_name, model_name,macAddress,createdDate, userEmail=None, ipAddress=None):
    if userEmail != None:
       userId = get_user_id(userEmail, api_key)
    else:
        userId = None

    try:
        if status_name == 'ACTIVE':
            status_id = 2 
        else:
            status_id = get_status_id(status_name, api_key)
    except Exception as e:
       print(e)
       status_id = 5
    model_id = get_model_id(model_name, api_key)



    hardware = {

        'assetTag': asset_tag, #Required This is the serial number of the hardware.
        'modelId': model_id, #Required This is the model id of the hardware.
        'statusId': status_id, # Required This is the status id.
        '_snipeit_mac_address_1': macAddress, #Optional
        '_snipeit_setupdate_2': createdDate, #Optional
        '_snipeit_ip_address_3': ipAddress, #Optional
        'assigned_user': userId  #Optional
    }


    url = f"{base_url}/hardware" 
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=hardware, headers=headers)
    return response.status_code, response.text
def get_model_id(name: str, api_key: str, base_url: str = base_url):
  """
  Retrieves the ID of a model in Snipe-IT using the provided name and API key.

  Args:
      name (str): The name of the model to search for.
      api_key (str): Your Snipe-IT API key.
      base_url (str, optional): The base URL of your Snipe-IT instance. Defaults to "https://your-snipeit-url/api/v1".

  Returns:
      int: The ID of the model if found, otherwise None.
  """

  # Construct the API endpoint URL with search parameter
  url = f"{base_url}/models?search={name}"

  # Set headers with the API key
  headers = {'Authorization': f'Bearer {api_key}'}

  try:
    # Send a GET request to the API endpoint
    response = requests.get(url, headers=headers)

    # Check for successful response (200 OK)
    if response.status_code == 200:
      data = json.loads(response.content)
      # Extract the ID from the first matching model (assuming unique names)
      if data['rows']:
        print(data['rows'])

        return data['rows'][0]['id']
      else:
        print(f"No model found with name: {name}")
        return None
    else:
      print(f"API request failed with status code: {response.status_code}")
      print(f"Response text: {response.text}")
      return None

  except requests.exceptions.RequestException as e:
    print(f"An error occurred while making the API request: {e}")
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
    headers = {'Authorization': f'Bearer {api_key}'}

    # Prepare the query parameters
    params = {'name': name}

    try:
        # Send a GET request to the API endpoint
        response = requests.get(url, headers=headers, params=params)

        # Check for successful response (200 OK)
        if response.status_code == 200:
            data = json.loads(response.content)
            # Extract the ID from the first matching status (assuming unique names)
            print(data)
            if data['rows']:
                return data['rows'][0]['id']
            else:
                print(f"No status found with name: {name}")
                return None
        else:
            print(f"API request failed with status code: {response.status_code}")
            print(f"Response text: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while making the API request: {e}")
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
    headers = {'Authorization': f'Bearer {api_key}'}
    params = {'email': email} 
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
      data = response.json()
      if data['rows']:
        return data['rows'][0]['id']
      else:
        print(f"No user found with email: {email}")
        return None 
    else:
      print(f"API request failed with status code: {response.status_code}")
      print(f"Response text: {response.text}")
      return None

  except requests.exceptions.RequestException as e:
    print(f"An error occurred while making the API request: {e}")
    return None

def check_out_device(user):
    pass
def check_in_device():
    pass

if __name__ == '__main__':
    devicedata = googleAuth.fetch_and_print_chromeos_devices()
    for device in devicedata:
        print(create_hardware(device.get('Serial Number'), device.get('Status'), device.get('Model'), device.get('Mac Address'), device.get('First Enrollment Time'), device.get('Device User'), device.get('Last Known IP Address')))
