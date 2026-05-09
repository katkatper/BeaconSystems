import requests

BASE_URL= "https://api.police-data.gov"

def fetch_Beacon_systems():
    response= requests.get(f"{BASE_URL}/missing")
    return response.json()


#connect to API

