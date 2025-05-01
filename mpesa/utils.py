import requests
import base64
from django.conf import settings
from datetime import datetime
from requests.auth import HTTPBasicAuth

def get_access_token():
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    auth_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

    response = requests.get(auth_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    response.raise_for_status()  # Will raise an error if token request fails
    return response.json().get('access_token')


def get_timestamp():
    return datetime.now().strftime('%Y%m%d%H%M%S')


def generate_password():
    timestamp = get_timestamp()
    shortcode = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY
    data_to_encode = shortcode + passkey + timestamp
    encoded_string = base64.b64encode(data_to_encode.encode()).decode()
    return encoded_string


def lipa_na_mpesa(phone_number, amount):
    access_token = get_access_token()
    api_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    timestamp = get_timestamp()

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": generate_password(),
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": "ElectroZone",
        "TransactionDesc": "Payment for goods"
    }

    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()
