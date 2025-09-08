from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from decimal import Decimal
from django.http import JsonResponse
from .models import Cart, CartItem, DeliveryLocation
from core.models import Product
from coupons.models import Coupon

# -----------------------------------------------------
# Helper function to get or create a cart
# -----------------------------------------------------
def get_cart(request):
    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        cart, _ = Cart.objects.get_or_create(session_key=session_key, user=None)
    return cart


# -----------------------------------------------------
# View Cart Page
# -----------------------------------------------------
def view_cart(request):
    cart = get_cart(request)
    items = cart.items.all()

    base_total = cart.get_total()  # already includes delivery fee if set
    coupon_discount = Decimal('0')
    discount_message = ""

    # Coupon handling
    if cart.coupon and cart.coupon.is_valid():
        if cart.coupon.discount_type == 'percentage':
            coupon_discount = base_total * Decimal(cart.coupon.discount_value) / Decimal('100')
            discount_message = f'Coupon "{cart.coupon.code}" applied! {cart.coupon.discount_value}% off'
        elif cart.coupon.discount_type == 'fixed':
            coupon_discount = Decimal(cart.coupon.discount_value)
            discount_message = f'Coupon "{cart.coupon.code}" applied! Ksh {coupon_discount} off'

    delivery_fee = cart.delivery_location.delivery_fee if cart.delivery_location else Decimal('0')
    delivery_message = f"Delivery Fee: Ksh {delivery_fee}" if cart.delivery_location else "Select a delivery location."

    delivery_locations = DeliveryLocation.objects.all()

    total_after_discount = max(base_total - coupon_discount, Decimal('0'))
    final_total = total_after_discount  # delivery already in base_total

    return render(request, 'cart/cart.html', {
        'cart': cart,
        'items': items,
        'base_total': base_total,
        'coupon_discount': coupon_discount,
        'discount_message': discount_message,
        'delivery_fee': delivery_fee,
        'delivery_message': delivery_message,
        'delivery_locations': delivery_locations,
        'total_after_discount': total_after_discount,
        'final_total': final_total,
    })


# -----------------------------------------------------
# Add to Cart
# -----------------------------------------------------
def add_to_cart(request, product_id):
    if request.method == "POST":
        cart = get_cart(request)
        product = get_object_or_404(Product, id=product_id)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()

        messages.success(request, f"{product.name} has been added to your cart.")
        return redirect("view_cart")  # send user to cart page

    return redirect("home")


# -----------------------------------------------------
# Remove from Cart
# -----------------------------------------------------
def remove_from_cart(request, item_id):
    if request.method == "POST":
        cart = get_cart(request)
        item = get_object_or_404(CartItem, id=item_id)

        if item.cart == cart:
            item.delete()
            messages.success(request, f"Removed {item.product.name} from your cart.")

        return redirect("view_cart")

    return redirect("home")


# -----------------------------------------------------
# Update Cart Quantity
# -----------------------------------------------------
def update_cart(request, item_id):
    if request.method == 'POST':
        cart = get_cart(request)
        item = get_object_or_404(CartItem, id=item_id)

        if item.cart == cart:
            try:
                quantity = int(request.POST.get('quantity', 1))
                if quantity > 0:
                    item.quantity = quantity
                    item.save()
                    messages.success(request, f"Updated quantity for {item.product.name}.")
                else:
                    item.delete()
                    messages.success(request, f"{item.product.name} removed from cart.")
            except ValueError:
                messages.error(request, "Invalid quantity input.")

        return redirect("view_cart")

    return redirect("home")


# -----------------------------------------------------
# Apply Coupon
# -----------------------------------------------------
def apply_coupon(request):
    cart = get_cart(request)
    if request.method == "POST":
        coupon_code = request.POST.get('coupon_code')
        try:
            coupon = Coupon.objects.get(code=coupon_code)

            if not coupon.is_valid():
                messages.error(request, "Coupon is expired or has reached its usage limit.")
                return redirect('view_cart')

            if cart.get_total() < coupon.min_purchase_amount:
                messages.error(request, f"Coupon requires a minimum purchase of Ksh {coupon.min_purchase_amount}.")
                return redirect('view_cart')

            cart.coupon = coupon
            cart.save()

            messages.success(request, f'Coupon "{coupon_code}" applied successfully.')
        except Coupon.DoesNotExist:
            messages.error(request, "Invalid coupon code.")

    return redirect('view_cart')


# -----------------------------------------------------
# Remove Coupon
# -----------------------------------------------------
def remove_coupon(request):
    cart = get_cart(request)
    if cart.coupon:
        cart.coupon = None
        cart.save()
        messages.success(request, "Coupon removed successfully.")
    else:
        messages.error(request, "No coupon to remove.")
    
    return redirect('view_cart')


# -----------------------------------------------------
# Set Delivery Location
# -----------------------------------------------------
def set_delivery_location(request):
    if request.method == 'POST':
        location_id = request.POST.get('location_id')
        cart = Cart.objects.filter(session_key=request.session.session_key).first()

        if not cart:
            return JsonResponse({"success": False, "message": "Cart not found"})

        if location_id:
            location = get_object_or_404(DeliveryLocation, id=location_id)
            cart.delivery_location = location
            cart.save()

            # Recalculate totals
            base_total = sum(item.get_subtotal() for item in cart.items.all())
            delivery_fee = location.delivery_fee
            coupon_discount = Decimal('0')

            if cart.coupon and cart.coupon.is_valid():
                if cart.coupon.discount_type == 'percentage':
                    coupon_discount = base_total * Decimal(cart.coupon.discount_value) / Decimal('100')
                elif cart.coupon.discount_type == 'fixed':
                    coupon_discount = Decimal(cart.coupon.discount_value)

            final_total = max(base_total - coupon_discount + delivery_fee, Decimal('0'))

            return JsonResponse({
                "success": True,
                "message": f"Delivery set to {location.area} (Ksh {delivery_fee})",
                "base_total": str(base_total),
                "delivery_fee": str(delivery_fee),
                "coupon_discount": str(coupon_discount),
                "final_total": str(final_total)
            })

        return JsonResponse({"success": False, "message": "Invalid location"})

    return JsonResponse({"success": False, "message": "Invalid request"})
