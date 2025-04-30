from django.db import models
from django.utils import timezone

class Coupon(models.Model):
    CODE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed'),
    ]
    
    code = models.CharField(max_length=50, unique=True)  # Unique coupon code
    discount_type = models.CharField(max_length=10, choices=CODE_CHOICES)  # Discount type (percentage or fixed)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)  # Discount amount
    expiry_date = models.DateField()  # Expiry date
    usage_limit = models.PositiveIntegerField(default=1)  # How many times it can be used
    used_count = models.PositiveIntegerField(default=0)  # Tracks usage count
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Minimum purchase requirement
    
    def is_valid(self):
        """Check if the coupon is still valid."""
        return self.expiry_date >= timezone.now().date() and self.used_count < self.usage_limit

    def apply_discount(self, cart_total):
        """Calculates the discount based on the coupon type and value."""
        if self.discount_type == 'percentage':
            return cart_total * (self.discount_value / 100)
        elif self.discount_type == 'fixed':
            return self.discount_value
        return 0

    def __str__(self):
        return f"Coupon {self.code}"
