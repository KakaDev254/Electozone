from django.shortcuts import render

# Create your views here.
from django.shortcuts import redirect
from django.views import View
from django.conf import settings
from .services import get_access_token
import requests
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

class PesaPalPaymentView(View):
    def get(self, request):
        token = get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        data = {
            "id": "ORDER123456",
            "currency": "KES",
            "amount": "1.00",
            "description": "BMW Spare Parts Order",
            "callback_url": settings.PESAPAL_CALLBACK_URL,
            "notification_id": "a193c2f7-b912-40ac-913d-dbab0d606180",  # Sandbox IPN ID
            "billing_address": {
                "email_address": "customer@example.com",
                "phone_number": "+254700123456",
                "country_code": "KE",
                "first_name": "John",
                "last_name": "Doe"
            }
        }

        url = "https://cybqa.pesapal.com/pesapalv3/api/Transactions/SubmitOrderRequest"
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        res_json = response.json()
        order_url = res_json.get("redirect_url")

        if order_url:
            return redirect(order_url)
        else:
            return HttpResponse(f"No redirect URL returned from Pesapal. Response: {res_json}", status=500)

@csrf_exempt
def pesapal_callback(request):
    # Handle Pesapal's callback or webhook data here
    return HttpResponse("Payment callback received.")
