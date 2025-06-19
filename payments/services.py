import requests
import os

PESAPAL_BASE_URL = "https://cybqa.pesapal.com/pesapalv3"

def get_access_token():
    url = f"{PESAPAL_BASE_URL}/api/Auth/RequestToken"
    headers = {'Content-Type': 'application/json'}
    data = {
        "consumer_key": os.getenv("PESAPAL_CONSUMER_KEY"),
        "consumer_secret": os.getenv("PESAPAL_CONSUMER_SECRET")
    }

    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    return response.json().get("token")
