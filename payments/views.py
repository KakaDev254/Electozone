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
    Initiates the PesaPal payment and redirects the user to the payment gateway.
    """
    order = get_object_or_404(Order, id=order_id)

    try:
        redirect_url = create_pesapal_order_url(order, request.user)
        return redirect(redirect_url)
    except Exception as e:
        logger.error(f"Payment initiation failed: {e}")
        return HttpResponseBadRequest("Failed to initiate payment. Please try again.")


def payment_callback(request):
    """
    Callback endpoint hit by PesaPal after user is redirected post-payment.
    """
    tracking_id = request.GET.get("OrderTrackingId")
    merchant_reference = request.GET.get("OrderMerchantReference")

    if not tracking_id or not merchant_reference:
        logger.warning("Callback missing tracking ID or merchant reference.")
        return HttpResponseBadRequest("Missing OrderTrackingId or OrderMerchantReference")

    try:
        token = get_pesapal_token()
        if not token:
            return HttpResponse("Failed to authenticate with PesaPal", status=500)

        payment_status = fetch_transaction_status(tracking_id, token)
        if not payment_status:
            return HttpResponse("Failed to retrieve payment status", status=500)

        order = get_object_or_404(Order, id=int(merchant_reference))

        # Avoid duplicate callbacks
        if order.pesapal_tracking_id and order.pesapal_tracking_id != tracking_id:
            logger.info(f"Duplicate callback received for Order {order.id}")
            return redirect('orders:order_success', order.id)

        if payment_status.upper() == "COMPLETED":
            try:
                order.pesapal_tracking_id = tracking_id
                order.mark_paid(reference=tracking_id)
                logger.info(f"Order {order.id} marked as paid.")
            except ValueError as e:
                logger.warning(f"Status transition failed: {e}")
                return HttpResponse(f"Status transition error: {e}", status=400)
            return redirect('orders:order_success', order.id)

        else:
            # Handle failure
            try:
                order.fail()
                logger.info(f"Order {order.id} marked as failed (status: {payment_status}).")
            except ValueError:
                logger.info(f"Order {order.id} already marked as failed.")
            return redirect('orders:order_failed', order.id)

    except Exception as e:
        logger.error(f"Error handling payment callback: {e}")
        return HttpResponse("An error occurred while processing the callback", status=500)


def pesapal_ipn_listener(request):
    """
    IPN endpoint hit by PesaPal asynchronously to confirm payment status.
    """
    if request.method == "POST":
        logger.info(f"IPN Received: {request.body}")
        # Optional: parse `request.body` and confirm status
        # Best practice: Re-check payment status using tracking ID and update order

        return HttpResponse("IPN received successfully")
    
    return HttpResponseBadRequest("Invalid method")
   
