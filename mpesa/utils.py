# payments/utils.py

import requests
import base64
import datetime
from django.conf import settings


def format_phone_number(phone_number):
    """Format phone numbers to Safaricom expected format: 2547XXXXXXXX."""
    if phone_number.startswith('0'):
        return '254' + phone_number[1:]
    elif phone_number.startswith('+'):
        return phone_number[1:]
    elif phone_number.startswith('7'):
        return '254' + phone_number
    return phone_number


def get_access_token():
    """Get M-Pesa API access token from Safaricom."""
    environment = settings.MPESA_ENVIRONMENT
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET

    if environment == 'production':
        auth_url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    else:
        auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    response = requests.get(auth_url, auth=(consumer_key, consumer_secret))
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        raise Exception("Failed to obtain M-Pesa access token")


def initiate_stk_push(phone_number, amount, order_id):
    """Initiate STK Push payment request."""
    # Load settings
    environment = settings.MPESA_ENVIRONMENT
    business_short_code = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY
    callback_url = settings.MPESA_CALLBACK_URL

    # Format phone number
    phone_number = format_phone_number(phone_number)

    # Get access token
    access_token = get_access_token()

    # Generate timestamp and password
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = business_short_code + passkey + timestamp
    password = base64.b64encode(data_to_encode.encode()).decode('utf-8')

    # STK Push URL
    stk_url = (
        "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        if environment == 'production'
        else "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "BusinessShortCode": business_short_code,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone_number,
        "PartyB": business_short_code,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": f"Order-{order_id}",
        "TransactionDesc": "Payment for ElectroZone Order",
    }

    stk_response = requests.post(stk_url, json=payload, headers=headers)
    return stk_response.json()
