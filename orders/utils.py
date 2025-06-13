# orders/utils.py

import uuid
import logging
import requests
from requests_oauthlib import OAuth1Session
from django.conf import settings

logger = logging.getLogger(__name__)

def get_pesapal_token():
    url = "https://cybqa.pesapal.com/pesapalv3/api/Auth/RequestToken"
    response = requests.get(
        url,
        auth=(settings.PESAPAL_CONSUMER_KEY, settings.PESAPAL_CONSUMER_SECRET)
    )
    response.raise_for_status()
    return response.json()["token"]


def fetch_transaction_status(tracking_id, token):
    """
    Check the status of a transaction using its tracking ID.
    """
    url = f"https://cybqa.pesapal.com/pesapalv3/api/Transactions/GetTransactionStatus?orderTrackingId={tracking_id}"
    try:
        response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()
        return response.json().get("payment_status")
    except requests.RequestException as e:
        logger.error(f"Error fetching transaction status for {tracking_id}: {e}")
        return None


def create_pesapal_order_url(order, user):
    token = get_pesapal_token()
    url = "https://cybqa.pesapal.com/api/Transactions/SubmitOrderRequest"

    payload = {
        "id": str(uuid.uuid4()),  # unique ID for this transaction
        "currency": "KES",
        "amount": float(order.get_total()),
        "description": f"Order #{order.id}",
        "callback_url": settings.PESAPAL_CALLBACK_URL,
        "notification_id": settings.PESAPAL_NOTIFICATION_ID,  # should be a valid ID from your merchant account
        "billing_address": {
            "email_address": user.email,
            "phone_number": user.profile.phone,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "line_1": "Nairobi",
            "city": "Nairobi",
            "state": "Nairobi",
            "postal_code": "00100",
            "country_code": "KE",
            "zip_code": "00100",
        },
        "merchant_reference": str(order.id),
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        logger.info(f"Sending order to Pesapal: {payload}")
        response = requests.post(url, json=payload, headers=headers)
        logger.info(f"Pesapal response: {response.status_code} - {response.text}")
        response.raise_for_status()

        result = response.json()
        redirect_url = result.get("redirect_url")

        if not redirect_url:
            raise Exception("No redirect_url returned by PesaPal")

        return redirect_url

    except Exception as e:
        logger.error(f"Pesapal payment initiation failed: {e}")
        raise

def get_notification_ids():
    """
    Retrieve registered IPN listener URLs and their IDs from PesaPal.
    """
    token = get_pesapal_token()
    if not token:
        logger.error("Could not retrieve token for IPN fetch")
        return []

    url = "https://cybqa.pesapal.com/pesapalv3/api/URLSetup/GetIpnList"
    headers = {
        "Authorization": f"Bearer {token}",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        ipns = response.json()
        for ipn in ipns:
            logger.info(f"Registered IPN: {ipn['url']} => ID: {ipn['id']}")
        return ipns

    except requests.RequestException as e:
        logger.error(f"Error fetching IPN list: {e}")
        return []