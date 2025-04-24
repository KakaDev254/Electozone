from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import OrderForm
from .models import Order, OrderItem
from cart.models import Cart

@login_required
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        return redirect('cart')  # Optional: redirect to cart if it's empty

    items = cart.items.all()

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.status = Order.PENDING  # Set the initial order status to PENDING
            order.save()

            # Create OrderItems from CartItems
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )

            # Clear the cart
            cart.items.all().delete()

            return redirect('order_success', order_id=order.id)  # Pass order ID to success page
    else:
        form = OrderForm()

    return render(request, 'orders/checkout.html', {
        'form': form,
        'items': items,
        'cart': cart,  # ✅ Add this line to pass cart to the template
    })


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/success.html', {'order': order})  # Pass order to the success page


@login_required
def order_history(request):
    orders = request.user.orders.prefetch_related('items__product').order_by('-created_at')
    return render(request, 'orders/order_history.html', {'orders': orders})  


@login_required
def change_order_status(request, order_id, status):
    """Handle the status change of an order."""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Validate status transition
    if status == Order.PAID and order.status == Order.PENDING:
        order.mark_paid()
    elif status == Order.PROCESSING and order.status == Order.PAID:
        order.start_processing()
    elif status == Order.SHIPPED and order.status == Order.PROCESSING:
        order.ship_order()
    elif status == Order.OUT_FOR_DELIVERY and order.status == Order.SHIPPED:
        order.out_for_delivery()
    elif status == Order.DELIVERED and order.status == Order.OUT_FOR_DELIVERY:
        order.deliver()
    elif status == Order.CANCELLED and order.status not in [Order.DELIVERED, Order.REFUNDED]:
        order.cancel()
    elif status == Order.REFUNDED and order.status == Order.PAID:
        order.refund()
    elif status == Order.FAILED and order.status == Order.PENDING:
        order.fail()

    return redirect('order_history')  # Redirect back to the order history page
