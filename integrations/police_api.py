import requests

from config.settings import EXTERNAL_API_TIMEOUT_SECONDS

BASE_URL= "https://api.police-data.gov"

def fetch_Beacon_systems():
    response = requests.get(
        f"{BASE_URL}/missing",
        timeout=EXTERNAL_API_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


#connect to API

