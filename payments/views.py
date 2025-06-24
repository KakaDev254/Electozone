# payments/views.py

from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.conf import settings
from .services import get_access_token
from orders.models import Order
import requests
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

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
            "notification_id": settings.PESAPAL_NOTIFICATION_ID,  # stored in .env
            "billing_address": {
                "email_address": order.user.email,
                "phone_number": order.phone_number,
                "first_name": order.user.first_name,
                "last_name": order.user.second_name,
                "country_code": "KE",
            }
        }

        url = "https://cybqa.pesapal.com/pesapalv3/api/Transactions/SubmitOrderRequest"
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

    # Get token again
    token = get_access_token()

    # Check transaction status
    url = f"https://cybqa.pesapal.com/pesapalv3/api/Transactions/GetTransactionStatus?orderTrackingId={tracking_id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    payment_status = response.json().get("payment_status")

    # Get the order using merchant_reference (order_number)
    order = get_object_or_404(Order, order_number=merchant_reference)

    if payment_status == "COMPLETED":
        order.mark_paid_with_tracking(reference=tracking_id, tracking_id=tracking_id)
    else:
        order.fail()

    return HttpResponse("Callback received and processed.")