from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseNotAllowed
from django.conf import settings
from django.shortcuts import render
import requests
import json
from .models import Payment 
from orders.models import Order
from .utils import get_access_token, generate_password, format_phone_number

# STK Push Request to initiate payment
@csrf_exempt
@login_required
def stk_push_request(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method. Use POST.'}, status=400)

    raw_phone = request.POST.get('phone')
    order_id = request.POST.get('order_id')

    # Validate order
    try:
        order = Order.objects.get(id=order_id, user=request.user, is_paid=False)
    except Order.DoesNotExist:
        return JsonResponse({'errorMessage': 'Order not found or already paid.'}, status=404)

    # Format and validate phone number
    phone = format_phone_number(raw_phone)
    if not phone or not phone.startswith("2547") or len(phone) != 12:
        return JsonResponse({'errorMessage': 'Invalid Safaricom number. Use formats like 0722XXXXXX or 2547XXXXXXX.'}, status=400)

    amount = order.get_total()  # Use server-verified amount

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
        "AccountReference": f"Order{order.id}",
        "TransactionDesc": f"Payment for Order #{order.id}"
    }

    response = requests.post(
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        headers=headers,
        data=json.dumps(payload)
    )

    try:
        response_data = response.json()
    except ValueError:
        return JsonResponse({'error': 'Failed to parse Safaricom response'}, status=500)

    if response_data.get("ResponseCode") == "0":
        Payment.objects.create(
            user=request.user,
            order=order,
            phone=phone,
            amount=amount,
            checkout_id=response_data.get("CheckoutRequestID"),
            status="pending"
        )

    return JsonResponse(response_data)



@csrf_exempt
def mpesa_callback(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'], "Only POST requests are allowed")

    try:
        data = json.loads(request.body.decode('utf-8'))
        print("Callback received:", json.dumps(data, indent=2))
    except json.JSONDecodeError:
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid JSON"}, status=400)

    # Extract result data
    result_code = data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
    checkout_id = data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
    result_desc = data.get('Body', {}).get('stkCallback', {}).get('ResultDesc')

    # Handle payment based on result code
    try:
        payment = Payment.objects.get(checkout_id=checkout_id)
        payment.message = result_desc

        if result_code == 0:
            payment.status = 'success'
        elif result_code == 1032:
            payment.status = 'cancelled'
        elif result_code == 1037:
            payment.status = 'timeout'
        elif result_code == 2001:
            payment.status = 'failed'
        else:
            payment.status = 'failed'

        payment.save()
    except Payment.DoesNotExist:
        print(f"CheckoutRequestID {checkout_id} not found in Payment table")

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
def payment_page(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    context = {
        'order': order,
        'amount': round(order.get_total(), 0),  # Ensure no decimal
        'phone': order.phone_number
    }
    return render(request, 'mpesa/payment.html', context)
