# payments/views.py

import logging
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, get_object_or_404
from orders.models import Order
from orders.utils import (
    get_pesapal_token,
    fetch_transaction_status,
    create_pesapal_order_url
)

logger = logging.getLogger(__name__)


def initiate_payment(request, order_id):
    """
    Initiates the PesaPal payment and redirects user to payment gateway.
    """
    order = get_object_or_404(Order, id=order_id)

    try:
        redirect_url = create_pesapal_order_url(order, request.user)
        return redirect(redirect_url)
    except Exception as e:
        logger.error(f"Payment initiation error: {e}")
        return HttpResponseBadRequest(f"Payment initiation failed: {e}")


def payment_callback(request):
    """
    Callback endpoint hit by PesaPal after payment is processed.
    """
    tracking_id = request.GET.get('OrderTrackingId')
    merchant_reference = request.GET.get('OrderMerchantReference')

    if not tracking_id or not merchant_reference:
        return HttpResponseBadRequest("Missing OrderTrackingId or OrderMerchantReference")

    token = get_pesapal_token()
    if not token:
        return HttpResponse("Failed to authenticate with PesaPal", status=500)

    payment_status = fetch_transaction_status(tracking_id, token)
    if not payment_status:
        return HttpResponse("Failed to fetch payment status", status=500)

    try:
        order = get_object_or_404(Order, id=int(merchant_reference))
    except ValueError:
        return HttpResponseBadRequest("Invalid OrderMerchantReference")

    if order.pesapal_tracking_id and order.pesapal_tracking_id != tracking_id:
        logger.warning(f"Duplicate callback for Order {order.id} with tracking ID {tracking_id}")
        return redirect('orders:order_success', order.id)

    if payment_status == "COMPLETED":
        try:
            order.pesapal_tracking_id = tracking_id
            order.mark_paid(reference=tracking_id)
        except ValueError as e:
            logger.warning(f"Status transition failed: {e}")
            return HttpResponse(f"Status transition error: {e}", status=400)
        return redirect('orders:order_success', order.id)
    else:
        try:
            order.fail()
        except ValueError:
            logger.info(f"Order {order.id} already marked as failed.")
        return redirect('orders:order_failed', order.id)
    

def pesapal_ipn_listener(request):
    if request.method == "POST":
        logger.info(f"IPN received: {request.body}")
        # Parse and handle the IPN data here
        return HttpResponse("IPN Received")
    return HttpResponseBadRequest("Invalid method")    
