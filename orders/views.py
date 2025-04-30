# orders/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import PermissionDenied
from .forms import OrderForm
from .models import Order, OrderItem
from cart.models import Cart
import logging

logger = logging.getLogger(__name__)


@login_required
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        messages.error(request, "Your cart is empty.")
        return redirect('cart')

    items = cart.items.all()

    if not items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('cart')

    # Get delivery fee from session
    delivery_fee = request.session.get('delivery_fee', 0)

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    order = form.save(commit=False)
                    order.user = request.user
                    order.status = Order.PENDING
                    order.save()

                    # Create OrderItems from the cart
                    for item in items:
                        OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            quantity=item.quantity,
                            price=item.product.price
                        )

                    # Clear the cart
                    cart.items.all().delete()

                    # Add delivery fee to the total amount of the order
                    order.total_amount = order.get_total() + delivery_fee
                    order.save()

                    # Redirect to payment page
                    return redirect('payment_page', order_id=order.id)

            except Exception as e:
                logger.error(f"Checkout failed: {e}")
                messages.error(request, "An error occurred during checkout.")
                return redirect('cart')
    else:
        form = OrderForm()

    return render(request, 'orders/checkout.html', {
        'form': form,
        'items': items,
        'cart': cart,
        'delivery_fee': delivery_fee,
    })


@login_required
def payment_page(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/payment.html', {'order': order})


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
