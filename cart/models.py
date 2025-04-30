# cart/models.py

from django.db import models
from django.conf import settings
from core.models import Product
from coupons.models import Coupon  # Import the Coupon model

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)  # Add this field to link the coupon

    def __str__(self):
        return f"Cart ({self.id}) for {self.user}"

    def get_total(self):
        total = sum(item.get_subtotal() for item in self.items.all())  # Calculate total from cart items
        if self.coupon:  # Apply the coupon discount if a coupon is applied
            if self.coupon.discount_type == 'percentage':
                total -= (self.coupon.discount_value / 100) * total  # Apply percentage discount
            else:
                total -= self.coupon.discount_value  # Apply fixed discount
        return total

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_subtotal(self):
        return self.product.price * self.quantity  # Calculate the subtotal for the cart item
    
class DeliveryLocation(models.Model):
    name = models.CharField(max_length=255)
    areas = models.TextField(help_text="Comma-separated areas covered")
    fee = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.name} – Ksh {self.fee}"    
