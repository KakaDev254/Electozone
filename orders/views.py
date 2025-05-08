# orders/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import PermissionDenied
from .forms import OrderForm
from .models import Order, OrderItem
from coupons.models import Coupon
from cart.models import Cart
import logging

logger = logging.getLogger(__name__)


def checkout_view(request):
    try:
        cart = Cart.objects.get(user=request.user)
        items = cart.items.all()
    except Cart.DoesNotExist:
        cart = None
        items = []

    delivery_fee = request.session.get("delivery_fee", 0)
    delivery_message = request.session.get("delivery_message", "")

    if request.method == 'POST':
        form = OrderForm(request.POST)

        if not cart or not items:
            messages.error(request, "Your cart is empty.")
            return redirect('cart_view')

        if form.is_valid():
            # Save the order
            order = form.save(commit=False)
            order.user = request.user
            order.status = Order.PENDING
            order.delivery_fee = delivery_fee or 0
            order.delivery_message = delivery_message or ""
            order.save()

            # Create order items
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )

            # Update coupon usage if applied
            if cart.coupon:
                cart.coupon.used_count += 1
                cart.coupon.save()

            # Clear cart after order is placed
            cart.items.all().delete()
            cart.coupon = None
            cart.save()

            return redirect('payment_page', order_id=order.id)
    else:
        form = OrderForm()

    subtotal = sum(item.get_subtotal() for item in items)

    return render(request, 'orders/checkout.html', {
        'form': form,
        'cart': cart,
        'items': items,
        'delivery_fee': delivery_fee,
        'delivery_message': delivery_message,
        'subtotal': subtotal,
    })



@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/success.html', {'order': order})


@login_required
def order_failure(request):
    order_id = request.GET.get('order_id')
    if order_id:
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            messages.error(request, 'Your payment failed. Please try again.')
        except Order.DoesNotExist:
            messages.error(request, 'Order not found.')
    else:
        messages.error(request, 'Invalid request.')

    return render(request, 'orders/failure.html')


@login_required
def order_history(request):
    orders = request.user.orders.prefetch_related('items__product').order_by('-created_at')
    return render(request, 'orders/order_history.html', {'orders': orders})


@login_required
def change_order_status(request, order_id, status):
    """Admin or user-triggered order status change."""
    if request.user.is_staff:
        order = get_object_or_404(Order, id=order_id)
    else:
        order = get_object_or_404(Order, id=order_id, user=request.user)

    # Valid status transitions
    STATUS_TRANSITIONS = {
        Order.PAID: [Order.PENDING],
        Order.PROCESSING: [Order.PAID],
        Order.SHIPPED: [Order.PROCESSING],
        Order.OUT_FOR_DELIVERY: [Order.SHIPPED],
        Order.DELIVERED: [Order.OUT_FOR_DELIVERY],
        Order.CANCELLED: [Order.PENDING, Order.PROCESSING, Order.SHIPPED, Order.OUT_FOR_DELIVERY],
        Order.REFUNDED: [Order.PAID],
        Order.FAILED: [Order.PENDING],
    }

    if status in STATUS_TRANSITIONS and order.status in STATUS_TRANSITIONS[status]:
        try:
            method = getattr(order, f"mark_{status.lower()}", None)
            if callable(method):
                method()
            else:
                logger.warning(f"Invalid status method: mark_{status.lower()} not found for order {order.id}")
                messages.error(request, "Invalid status change.")
        except Exception as e:
            logger.error(f"Status change failed: {e}")
            messages.error(request, "Failed to update order status.")
    else:
        logger.warning(f"Unauthorized or invalid status transition for order {order.id}: {order.status} -> {status}")
        messages.error(request, "Invalid or unauthorized status change.")

    return redirect('order_history')
