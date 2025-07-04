import requests
import json
import logging

from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from .services import get_access_token
from orders.models import Order

logger = logging.getLogger(__name__)


class PesaPalPaymentView(View):
    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        token = get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        data = {
            "id": str(order.order_number),  # used as unique ID
            "currency": "KES",
            "amount": str(order.get_total()),
            "description": f"Order #{order.id}",
            "callback_url": settings.PESAPAL_CALLBACK_URL,
            "notification_id": settings.PESAPAL_NOTIFICATION_ID,
            "billing_address": {
                "email_address": order.user.email,
                "phone_number": order.phone_number,
                "first_name": order.user.first_name,
                "last_name": order.user.second_name,
                "country_code": "KE",
            }
        }

        url = "https://pay.pesapal.com/v3/api/Transactions/SubmitOrderRequest"
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        order_url = response.json().get("redirect_url")
        if order_url:
            return redirect(order_url)
        else:
            return HttpResponse(f"No redirect URL returned. Response: {response.json()}", status=500)


@csrf_exempt
def pesapal_callback(request):
    tracking_id = request.GET.get('OrderTrackingId')
    merchant_reference = request.GET.get('OrderMerchantReference')

    if not tracking_id or not merchant_reference:
        return HttpResponse("Missing tracking ID or merchant reference", status=400)

    token = get_access_token()

    url = f"https://pay.pesapal.com/v3/api/Transactions/GetTransactionStatus?orderTrackingId={tracking_id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    payment_status = response.json().get("payment_status")
    order = get_object_or_404(Order, order_number=merchant_reference)

    if payment_status == "COMPLETED":
        order.mark_paid_with_tracking(reference=tracking_id, tracking_id=tracking_id)
    else:
        order.fail()

    return HttpResponse("Callback received and processed.")


@csrf_exempt
def pesapal_ipn_listener(request):
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            logger.info("✅ Received IPN: %s", payload)

            tracking_id = payload.get("OrderTrackingId")
            merchant_reference = payload.get("OrderMerchantReference")

            if not tracking_id or not merchant_reference:
                logger.warning("⚠️ Missing required fields in IPN payload")
                return HttpResponse("Missing fields", status=400)

            token = get_access_token()

            url = f"https://pay.pesapal.com/v3/api/Transactions/GetTransactionStatus?orderTrackingId={tracking_id}"
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            payment_status = response.json().get("payment_status")
            order = get_object_or_404(Order, order_number=merchant_reference)

            if payment_status == "COMPLETED":
                order.mark_paid_with_tracking(reference=tracking_id, tracking_id=tracking_id)
                logger.info(f"✅ Order {order.order_number} marked as PAID via IPN")
            else:
                order.fail()
                logger.info(f"❌ Order {order.order_number} marked as FAILED via IPN")

            return HttpResponse("IPN processed successfully", status=200)

        except json.JSONDecodeError:
            logger.error("❌ Invalid JSON received in IPN")
            return HttpResponse("Invalid JSON", status=400)

        except Exception as e:
            logger.exception("❌ IPN processing error")
            return HttpResponse(f"Server error: {str(e)}", status=500)

    return HttpResponse("Method Not Allowed", status=405)
