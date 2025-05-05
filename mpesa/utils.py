import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth
from datetime import datetime
import base64
import re

def format_phone_number(raw_phone):
    """
    Accepts various Kenyan number formats and converts to '2547XXXXXXXX'
    """
    phone = re.sub(r'\D', '', raw_phone)  # Remove all non-digit characters

    if phone.startswith("0") and len(phone) == 10:
        return "254" + phone[1:]
    elif phone.startswith("7") and len(phone) == 9:
        return "254" + phone
    elif phone.startswith("254") and len(phone) == 12:
        return phone
    elif phone.startswith("1") or phone.startswith("2"):
        return None  # Safaricom numbers typically start with 7
    elif phone.startswith("2547") and len(phone) == 12:
        return phone
    elif phone.startswith("+254") and len(phone) == 13:
        return phone[1:]
    else:
        return None


def get_access_token():
    url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    if settings.MPESA_ENVIRONMENT == 'production':
        url = url.replace('sandbox', 'api')

    response = requests.get(url, auth=HTTPBasicAuth(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET))
    return response.json().get('access_token')

def generate_password():
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    data = settings.MPESA_SHORTCODE + settings.MPESA_PASSKEY + timestamp
    password = base64.b64encode(data.encode()).decode()
    return password, timestamp
