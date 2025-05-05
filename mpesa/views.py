from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import render
import requests
import json
from .models import Payment 
from .utils import get_access_token, generate_password, format_phone_number

# STK Push Request to initiate payment
@csrf_exempt
def stk_push_request(request):
    if request.method == 'POST':
        raw_phone = request.POST.get('phone')
        amount = request.POST.get('amount')

        phone = format_phone_number(raw_phone)

        if not phone or not phone.startswith("2547") or len(phone) != 12:
            return JsonResponse({'errorMessage': 'Invalid Safaricom number. Use formats like 0723XXXXXX or 2547XXXXXXX.'}, status=400)

        access_token = get_access_token()
        password, timestamp = generate_password()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone,
            "CallBackURL": settings.MPESA_CALLBACK_URL,
            "AccountReference": "ElectroZone",
            "TransactionDesc": "Payment for goods"
        }

        response = requests.post(
            "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
            headers=headers,
            data=json.dumps(payload)
        )

        response_data = response.json()

        # Save the payment in the database to track callback
        if response_data.get("ResponseCode") == "0":
            Payment.objects.create(
                phone=phone,
                amount=amount,
                checkout_id=response_data.get("CheckoutRequestID"),
                status="pending"
            )

        return JsonResponse(response_data)

    return JsonResponse({'error': 'Invalid request method. Use POST.'}, status=400)

# MPesa Callback view to handle STK result
@csrf_exempt
def mpesa_callback(request):
    # Parse the JSON payload from M-Pesa
    data = json.loads(request.body.decode('utf-8'))
    print("Callback received:", json.dumps(data, indent=2))

    # Extract result data
    result_code = data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
    checkout_id = data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
    result_desc = data.get('Body', {}).get('stkCallback', {}).get('ResultDesc')

    # Handle payment based on result code
    try:
        payment = Payment.objects.get(checkout_id=checkout_id)
        payment.message = result_desc

        # Update payment status based on result code
        if result_code == 0:  # Success
            payment.status = 'success'
        elif result_code == 1032:  # User cancelled
            payment.status = 'cancelled'
        elif result_code == 1037:  # Timeout
            payment.status = 'timeout'
        elif result_code == 2001:  # Incorrect PIN
            payment.status = 'failed'
        else:  # Other error codes
            payment.status = 'failed'

        payment.save()

    except Payment.DoesNotExist:
        print(f"CheckoutRequestID {checkout_id} not found in Payment table")

    # Respond with a success message back to M-Pesa to confirm callback processing
    return JsonResponse({"ResultCode": 0, "ResultDesc": "Callback received successfully"})


# Endpoint to check the payment status
def payment_status(request):
    checkout_id = request.GET.get("checkout_id")
    if not checkout_id:
        return JsonResponse({"error": "checkout_id not provided"}, status=400)

    try:
        payment = Payment.objects.get(checkout_id=checkout_id)
        if payment.status == "pending":
            return JsonResponse({"status": "pending"})
        return JsonResponse({
            "status": payment.status,
            "message": payment.message,
            "success": payment.status == "success"
        })
    except Payment.DoesNotExist:
        return JsonResponse({"status": "pending"})

# Payment page rendering
def payment_page(request):
    return render(request, 'mpesa/payment.html')
