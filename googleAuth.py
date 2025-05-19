from googleapiclient.discovery import build
from google.oauth2 import service_account
import os

# Define the required scope
SCOPES = ['https://www.googleapis.com/auth/admin.directory.device.chromeos']

# Path to the service account key file
SERVICE_ACCOUNT_FILE = 'service_account.json'

# The admin email to impersonate (for domain-wide delegation)
DELEGATED_ADMIN = 'tgunnadmin@clearbrook-gonvick.k12.mn.us'  # ← Replace with your admin account

def bytes_to_gb(bytes_value):
  """Converts bytes to gigabytes."""
  return bytes_value / (1024 * 1024 * 1024)

def auth():
  """
  Authenticates using a Google service account with domain-wide delegation.

  Returns:
    google.auth.credentials.Credentials: Authenticated credentials object.
  """
  try:
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES)

    # Enable domain-wide delegation
    delegated_credentials = credentials.with_subject(DELEGATED_ADMIN)
    return delegated_credentials

  except Exception as e:
    print(f"Error loading service account credentials: {e}")
    return None

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
        maxResults=1500,
        orderBy='lastSync',
        sortOrder='DESCENDING',
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