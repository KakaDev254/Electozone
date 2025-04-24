from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.sessions.models import Session
from django.contrib import messages
from .models import Cart, CartItem
from core.models import Product

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
    return render(request, 'cart/cart.html', {'cart': cart, 'items': items})


# Add to Cart View (POST-based)
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
