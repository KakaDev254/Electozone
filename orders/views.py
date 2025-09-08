from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
from django.core.exceptions import PermissionDenied
from .forms import OrderForm
from .models import Order, OrderItem
from coupons.models import Coupon
from cart.models import Cart
import logging

logger = logging.getLogger(__name__)

def checkout_view(request):
    try:
        # Get cart: for guest users, we use session_id
        cart = Cart.objects.get(id=request.session.get("cart_id"))
        items = cart.items.all()
    except Cart.DoesNotExist:
        cart = None
        items = []

    # Delivery fee
    delivery_fee = cart.delivery_location.delivery_fee if cart and cart.delivery_location else Decimal("0")
    delivery_message = (
        f"Delivery Fee: Ksh {delivery_fee}"
        if cart and cart.delivery_location
        else "Select a delivery location to view delivery fee."
    )

    # Coupon discount
    coupon_discount = Decimal("0")
    discount_message = ""

    if cart and cart.coupon and cart.coupon.is_valid():
        if cart.coupon.discount_type == "percentage":
            coupon_discount = cart.get_total() * Decimal(cart.coupon.discount_value) / Decimal("100")
            discount_message = f'Coupon "{cart.coupon.code}" applied! Discount: {cart.coupon.discount_value}% off'
        elif cart.coupon.discount_type == "fixed":
            coupon_discount = Decimal(cart.coupon.discount_value)
            discount_message = f'Coupon "{cart.coupon.code}" applied! Discount: Ksh {coupon_discount}'

    # Totals
    base_total = cart.get_total() if cart else Decimal("0")
    items_total = sum(item.get_subtotal() for item in items)
    total_after_discount = max(base_total - coupon_discount, Decimal("0"))
    final_total = total_after_discount + delivery_fee   # ✅ include delivery fee

    if request.method == "POST":
        form = OrderForm(request.POST)

        if not cart or not items:
            messages.error(request, "Your cart is empty.")
            return redirect("view_cart")

        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)

                # No login required → optional user
                if request.user.is_authenticated:
                    order.user = request.user
                else:
                    order.user = None

                order.status = Order.PENDING
                order.delivery_fee = delivery_fee
                order.delivery_message = delivery_message
                order.coupon = cart.coupon if cart and cart.coupon else None
                order.total_amount = final_total   # ✅ save total amount
                order.save()

                # Save order items
                for item in items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.product.price,
                    )

                # Update coupon usage
                if cart.coupon:
                    cart.coupon.used_count += 1
                    cart.coupon.save()

                # Clear cart
                cart.items.all().delete()
                cart.coupon = None
                cart.save()

                return redirect("order_success", order_id=order.id)
    else:
        form = OrderForm()

    return render(
        request,
        "orders/checkout.html",
        {
            "form": form,
            "cart": cart,
            "items": items,
            "items_total": items_total,
            "base_total": base_total,
            "coupon_discount": coupon_discount,
            "discount_message": discount_message,
            "delivery_fee": delivery_fee,
            "delivery_message": delivery_message,
            "total_after_discount": total_after_discount,
            "final_total": final_total,
        },
    )
def order_success(request, order_id):
    # allow both guest & logged-in users
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/success.html', {'order': order})


def order_failure(request):
    """
    Not really used in COD flow,
    but kept for compatibility if you add payments later.
    """
    order_id = request.GET.get('order_id')
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
            messages.error(request, 'Your payment failed. Please try again.')
        except Order.DoesNotExist:
            messages.error(request, 'Order not found.')
    else:
        messages.error(request, 'Invalid request.')
    return render(request, 'orders/failure.html')





def change_order_status(request, order_id, status):
    """Admin or user-triggered order status change with controlled transitions."""
    if request.user.is_staff:
        order = get_object_or_404(Order, id=order_id)
    else:
        order = get_object_or_404(Order, id=order_id, user=request.user)

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

    if not request.user.is_staff:
        allowed_user_transitions = {
            Order.CANCELLED: [Order.PENDING, Order.PROCESSING],
        }
        if status not in allowed_user_transitions or order.status not in allowed_user_transitions[status]:
            raise PermissionDenied("You are not allowed to change the status.")

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
