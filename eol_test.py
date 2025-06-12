import requests
import pandas as pd
from datetime import datetime, timedelta
from mosyle_test import test
DEVICE_URL = "https://api.appledb.dev/device/main.json"
IOS_URL = "https://api.appledb.dev/ios/main.json"
from packaging.version import InvalidVersion
from datetime import datetime, timedelta
from packaging import version
from packaging.version import InvalidVersion

def estimate_device_eol(identifiers, ios_data, device_release):
    # Filter supported versions
    supported_versions = [
        ios for ios in ios_data
        if ios.get("released")
        and ios.get("osStr", "").startswith(("iOS", "iPadOS"))
        and any(identifier in ios.get("deviceMap", []) for identifier in identifiers)
    ]

    if not supported_versions:
        return "Unknown", "Unknown", "Unknown", "No iOS support found"

    # Sort by release date
    supported_versions.sort(
        key=lambda x: x["released"][0] if isinstance(x["released"], list) else x["released"]
    )

    latest_supported = supported_versions[-1]
    last_os_str = latest_supported["osStr"]
    release_raw = latest_supported["released"]
    release_str = release_raw[0] if isinstance(release_raw, list) else release_raw
    last_release = datetime.strptime(release_str, "%Y-%m-%d")

    # Look for newer versions that do NOT include this device
    newer_releases_exclude_device = [
        ios for ios in ios_data
        if ios.get("released")
        and ios.get("osStr", "").startswith(("iOS", "iPadOS"))
        and datetime.strptime(
            ios["released"][0] if isinstance(ios["released"], list) else ios["released"], "%Y-%m-%d"
        ) > last_release
        and not any(identifier in ios.get("deviceMap", []) for identifier in identifiers)
    ]

    # If excluded from newer releases, consider 1 year from last supported release
    if newer_releases_exclude_device:
        estimated_eol = last_release + timedelta(days=365)
    else:
        # Otherwise, fallback to release-based (6-year) EOL or 1-year-after-last-release
        release_based_eol = (
            device_release + timedelta(days=6 * 365)
            if device_release else last_release + timedelta(days=365)
        )
        estimated_eol = release_based_eol

    status = "EOL" if datetime.today() > estimated_eol else "Supported"
    return last_os_str, release_str, estimated_eol.strftime("%Y-%m-%d"), status


def get_ipad_eol(identifiers_list):
    devices = requests.get(DEVICE_URL).json()
    ios_data = requests.get(IOS_URL).json()

    results = []

    for identifier in identifiers_list:
        match = next((d for d in devices if identifier in d.get("identifier", [])), None)
        if not match:
            results.append({
                "identifier": identifier,
                "last_supported_ios": "Unknown",
                "ipad_release_date": "Unknown",
                "last_release_date": "Unknown",
                "estimated_eol": "Unknown",
                "status": "Not found"
            })
            continue

        release_date_str = match.get("released", None)
        name = match.get("name", None)
        model = match.get("model", ["Unknown"])[0]
        if isinstance(release_date_str, list):
            release_date_str = release_date_str[0]
        release_date = datetime.strptime(release_date_str, "%Y-%m-%d") if release_date_str else None

        ios_str, release, eol, status = estimate_device_eol([identifier], ios_data, release_date)

        results.append({
            "name": name,
            "identifier": identifier,
            "model": model,
            "last_supported_ios": ios_str,
            "ipad_release_date": release_date,
            "last_release_date": release,
            "estimated_eol": eol,
            "status": status
        })

    return pd.DataFrame(results)

# Example usage with device identifiers
devices = test()
ipad_identifiers = []
for device in devices:
    ipad_identifiers.append(device.get('device_model', None))
ipad_identifiers.append('iPad6,11')
df = get_ipad_eol(ipad_identifiers)
df.to_csv("ipad_eol_by_identifier_report.csv", index=False)
print(df)

