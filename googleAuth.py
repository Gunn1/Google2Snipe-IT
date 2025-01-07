from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import os
# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/admin.directory.device.chromeos']


def bytes_to_gb(bytes_value):
  """Converts bytes to gigabytes.

  Args:
    bytes_value: The number of bytes to convert.

  Returns:
    The number of gigabytes.
  """
  return bytes_value / (1024 * 1024 * 1024)

def auth():
  """
  Performs OAuth 2.0 authentication for the Google Admin SDK.

  This function handles the following:

    1. **Load Credentials:** 
       - Attempts to load existing credentials from 'token.json'.
       - Handles potential errors during loading.

    2. **Refresh Credentials:**
       - If the existing credentials are expired but have a refresh token, 
         attempts to refresh them.
       - Handles potential errors during the refresh process.

    3. **Initiate OAuth 2.0 Flow:** 
       - If no valid credentials are found, initiates the OAuth 2.0 flow 
         using 'credentials.json' to obtain user consent.
       - Handles potential errors during the OAuth 2.0 flow.

    4. **Save Credentials:**
       - Saves the obtained or refreshed credentials to 'token.json' for future use.
       - Handles potential errors during credential saving.

  Returns:
    - `google.oauth2.credentials.Credentials`: The authenticated credentials 
      object on successful authentication.
    - `None`: If an error occurs at any stage of the authentication process.
  """

  creds = None
  if os.path.exists('token.json'):
    try:
      creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    except Exception as e:
      print(f"Error loading credentials from token.json: {e}")
      return None

  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      try:
        creds.refresh(Request())
      except Exception as e:
        print(f"Error refreshing access token: {e}")
        return None
    else:
      try:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)  # Replace with your credentials file
        creds = flow.run_local_server(port=0)
      except Exception as e:
        print(f"Error during OAuth 2.0 flow: {e}")
        return None

    try:
      with open('token.json', 'w') as token:
        token.write(creds.to_json())
    except Exception as e:
      print(f"Error saving credentials to token.json: {e}")
      return None

  return creds

def fetch_and_print_chromeos_devices():
  """
  Fetches and displays information about Chrome OS devices in the user's 
  Google Workspace domain using the Google Admin SDK Directory API.

  This function:
    1. Authenticates with the Google Admin SDK using the `auth()` function.
    2. Calls the Chrome OS Devices API to retrieve a list of devices.
    3. Prints basic information about each device, including:
       - Recent user email 
       - Device ID
       - Serial Number
       - Status
    4. Handles potential errors during API calls or data processing.

  Requires a 'credentials.json' file with OAuth 2.0 client credentials 
  and saves authentication tokens to 'token.json' for future use.
  """

  creds = auth()

  if not creds:
    print("Authentication failed. Exiting.")
    return

  try:
    service = build('admin', 'directory_v1', credentials=creds)

    results = service.chromeosdevices().list(
        customerId='my_customer',  # Use "my_customer" for the current user's domain
        maxResults=600,
        orderBy='lastSync',
        sortOrder='ASCENDING',
        projection='FULL').execute()

    devices = results.get('chromeosdevices', [])
    device_data = []
    if not devices:
      print('No Chrome OS devices found.')
    else:
      print('Chrome OS devices:')
      for device in devices:
        device_info = {
          'Device User': device.get("recentUsers", [{}])[0].get("email"),
          'Serial Number': device.get("serialNumber"),
          'Status': device.get("status"),
          'Last Sync Time': device.get("lastSync"),
          'Model': device.get("model"),
          'Active Time Ranges': device.get("activeTimeRanges"),
          'Mac Address': device.get("macAddress"),
          'Last Known IP Address': device.get("lastKnownNetwork", [{}])[0].get("ipAddress"),
          'First Enrollment Time': device.get("firstEnrollmentTime") 
        }
        device_data.append(device_info)
      return device_data

  except Exception as error:
    print(f'An error occurred while interacting with the API: {error}')

if __name__ == '__main__':
  print(fetch_and_print_chromeos_devices())