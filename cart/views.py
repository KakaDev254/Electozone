from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from decimal import Decimal
from .models import Cart, CartItem, DeliveryLocation
from core.models import Product
from coupons.models import Coupon

# Helper function to get or create a cart
def get_cart(request):
    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        cart, _ = Cart.objects.get_or_create(session_key=session_key, user=None)
    return cart

# View Cart Page
def view_cart(request):
    cart = get_cart(request)
    items = cart.items.all()

    base_total = cart.get_total()  # This already includes delivery_fee if set on the cart
    coupon_discount = Decimal('0')
    discount_message = ""

    if cart.coupon and cart.coupon.is_valid():
        if cart.coupon.discount_type == 'percentage':
            coupon_discount = base_total * Decimal(cart.coupon.discount_value) / Decimal('100')
            discount_message = f'Coupon "{cart.coupon.code}" applied! Discount: {cart.coupon.discount_value}% off'
        elif cart.coupon.discount_type == 'fixed':
            coupon_discount = Decimal(cart.coupon.discount_value)
            discount_message = f'Coupon "{cart.coupon.code}" applied! Discount: Ksh {coupon_discount}'

    # Remove session-based delivery_fee usage to avoid duplication
    delivery_fee = cart.delivery_location.delivery_fee if cart.delivery_location else Decimal('0')
    delivery_message = f"Delivery Fee: Ksh {delivery_fee}" if cart.delivery_location else "Select a delivery location to view delivery fee."

    delivery_locations = DeliveryLocation.objects.all()

    total_after_discount = max(base_total - coupon_discount, Decimal('0'))
    final_total = total_after_discount  # No need to add delivery_fee again

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

# Add to Cart View
def add_to_cart(request, product_id):
    if request.method == "POST":
        cart = get_cart(request)
        product = get_object_or_404(Product, id=product_id)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()

        messages.success(request, f"{product.name} has been added to your cart.")
        return redirect("product_detail", pk=product.id)

    return redirect("home")

# Remove from Cart
def remove_from_cart(request, item_id):
    if request.method == "POST":
        cart = get_cart(request)
        item = get_object_or_404(CartItem, id=item_id)

        if item.cart == cart:
            item.delete()
            messages.success(request, f"Removed {item.product.name} from your cart.")

        return redirect("view_cart")

    return redirect("home")

# Update Cart Quantity
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
# Apply Coupon
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

            if coupon.discount_type == 'percentage':
                discount = cart.get_total() * Decimal(coupon.discount_value) / Decimal('100')
            elif coupon.discount_type == 'fixed':
                discount = Decimal(coupon.discount_value)
            else:
                discount = Decimal('0')

            messages.success(request, f'Coupon "{coupon_code}" applied! Discount: Ksh {discount}')
        except Coupon.DoesNotExist:
            messages.error(request, "Invalid coupon code.")

    return redirect('view_cart')

def remove_coupon(request):
    cart = get_cart(request)  # Use get_cart to get or create the cart for the user

    if cart.coupon:  # Check if there's an applied coupon
        cart.coupon = None  # Remove the coupon
        cart.save()
        messages.success(request, "Coupon removed successfully.")
    else:
        messages.error(request, "No coupon to remove.")
    
    return redirect('view_cart') 

# Set Delivery Location
def set_delivery_location(request):
    if request.method == 'POST':
        location_id = request.POST.get('location_id')

        if location_id:
            selected_location = get_object_or_404(DeliveryLocation, id=location_id)
            cart = get_cart(request)
            cart.delivery_location = selected_location
            cart.save()

            # Save as string to avoid Decimal JSON serialization issue
            request.session['delivery_fee'] = str(selected_location.delivery_fee)
            request.session['delivery_message'] = f"Delivery to {selected_location.area} - Ksh {selected_location.delivery_fee}"
            messages.success(request, f"Delivery location set to {selected_location.area} (Ksh {selected_location.delivery_fee})")
        else:
            messages.error(request, "Please select a delivery location.")

        return redirect('view_cart')

    cart = get_cart(request)
    delivery_locations = DeliveryLocation.objects.all()
    return render(request, 'cart/cart.html', {
        'delivery_locations': delivery_locations,
        'cart': cart,
    })
