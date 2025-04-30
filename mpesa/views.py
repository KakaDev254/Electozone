from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils.timezone import now
from django.utils.dateparse import parse_datetime
from django.conf import settings

import base64
import json
import requests
import logging

from .models import MpesaPayment
from orders.models import Order

logger = logging.getLogger(__name__)

@login_required
def initiate_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == "POST":
        phone = request.POST.get("phone")
        amount = float(order.get_total())

        timestamp = now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(
            (settings.MPESA_SHORTCODE + settings.MPESA_PASSKEY + timestamp).encode()
        ).decode()

        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone,
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone,
            "CallBackURL": settings.MPESA_CALLBACK_URL,
            "AccountReference": f"Order-{order.id}",
            "TransactionDesc": f"Payment for Order #{order.id}",
        }

        headers = {
            "Authorization": f"Bearer {settings.MPESA_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                settings.MPESA_STK_PUSH_URL, headers=headers, json=payload, timeout=30
            )
            data = response.json()
            logger.info("STK Push response: %s", data)

            if response.status_code == 200 and data.get("ResponseCode") == "0":
                payment = MpesaPayment.objects.create(
                    user=request.user,
                    order=order,
                    phone_number=phone,
                    amount=amount,
                    merchant_request_id=data["MerchantRequestID"],
                    checkout_request_id=data["CheckoutRequestID"],
                    status="PENDING",
                )
                return render(request, "mpesa_payment.html", {
                    "order": order,
                    "message": "STK Push sent to your phone. Complete payment.",
                    "merchant_request_id": payment.merchant_request_id,
                })
            else:
                return render(request, "mpesa_payment.html", {
                    "order": order,
                    "message": f"Payment initiation failed: {data.get('errorMessage', 'Try again')}",
                })

        except requests.RequestException as e:
            logger.error("Error sending STK Push: %s", e)
            return render(request, "mpesa_payment.html", {
                "order": order,
                "message": "Error sending STK Push. Please try again later.",
            })

    return render(request, "mpesa_payment.html", {"order": order})


@csrf_exempt
def mpesa_callback(request):
    data = json.loads(request.body)
    logger.info("M-Pesa Callback: %s", json.dumps(data, indent=2))

    stk_callback = data.get("Body", {}).get("stkCallback", {})

    result_code = stk_callback.get("ResultCode")
    result_desc = stk_callback.get("ResultDesc")
    callback_metadata = stk_callback.get("CallbackMetadata", {})

    items = callback_metadata.get("Item", [])
    item_dict = {item["Name"]: item.get("Value") for item in items}

    phone_number = str(item_dict.get("PhoneNumber", ""))
    amount = float(item_dict.get("Amount", 0))
    mpesa_receipt_number = item_dict.get("MpesaReceiptNumber")
    transaction_date_raw = str(item_dict.get("TransactionDate", ""))
    transaction_date = None

    if transaction_date_raw:
        transaction_date = parse_datetime(
            f"{transaction_date_raw[:4]}-{transaction_date_raw[4:6]}-{transaction_date_raw[6:8]}T{transaction_date_raw[8:10]}:{transaction_date_raw[10:12]}:{transaction_date_raw[12:14]}"
        )

    order_reference = stk_callback.get("AccountReference", "")
    order_id = order_reference.split("-")[-1]

    try:
        order = Order.objects.get(id=order_id)
        payment = MpesaPayment.objects.filter(order=order).order_by('-created_at').first()
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found.'}, status=404)

    if result_code == 0:
        if hasattr(order, "mark_paid"):
            order.mark_paid(reference=mpesa_receipt_number)
        order.save()

        if payment:
            payment.status = "Completed"
            payment.mpesa_receipt_number = mpesa_receipt_number
            payment.transaction_date = transaction_date
            payment.result_code = str(result_code)
            payment.result_description = result_desc
            payment.save()
        else:
            MpesaPayment.objects.create(
                order=order,
                phone_number=phone_number,
                amount=amount,
                mpesa_receipt_number=mpesa_receipt_number,
                transaction_date=transaction_date,
                result_code=str(result_code),
                result_description=result_desc,
                status="Completed"
            )
    else:
        if hasattr(order, "fail"):
            order.fail()
        order.save()

        if payment:
            payment.status = "Failed"
            payment.result_code = str(result_code)
            payment.result_description = result_desc
            payment.save()
        else:
            MpesaPayment.objects.create(
                order=order,
                phone_number=phone_number,
                amount=amount,
                result_code=str(result_code),
                result_description=result_desc,
                status="Failed"
            )

    return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})


@require_GET
@login_required
def check_payment_status(request, merchant_request_id):
    try:
        payment = MpesaPayment.objects.get(
            merchant_request_id=merchant_request_id,
            order__user=request.user
        )
    except MpesaPayment.DoesNotExist:
        return JsonResponse({'result': 'NOT_FOUND'}, status=404)

    return JsonResponse({'result': payment.status.upper()})


@login_required
def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    payment = MpesaPayment.objects.filter(order=order, status='Completed').first()
    return render(request, 'orders/payment_success.html', {'order': order, 'payment': payment})


@login_required
def cancel_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.status = 'Cancelled'
    order.save()
    messages.info(request, "Payment was cancelled.")
    return redirect("view_cart")
