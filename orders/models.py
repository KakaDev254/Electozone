from django.db import models
from django.conf import settings
from core.models import Product
from decimal import Decimal
import uuid


class Order(models.Model):
    # --- Status Constants ---
    PENDING = 'pending'
    PROCESSING = 'processing'
    SHIPPED = 'shipped'
    OUT_FOR_DELIVERY = 'out_for_delivery'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'

    ORDER_STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (SHIPPED, 'Shipped'),
        (OUT_FOR_DELIVERY, 'Out for Delivery'),
        (DELIVERED, 'Delivered'),
        (CANCELLED, 'Cancelled'),
    ]

    # --- Core Order Info ---
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    order_number = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default=PENDING)

    # --- Address Fields ---
    address = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)

    # --- Delivery & Contact ---
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_message = models.CharField(max_length=255, blank=True, null=True)

    # --- Coupon Reference ---
    coupon = models.ForeignKey('coupons.Coupon', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Order {self.id} - {self.user.email} ({self.status})"

    @property
    def email(self):
        return self.user.email

    def get_items_total(self):
        return sum(item.get_subtotal() for item in self.items.all())

    def apply_coupon_discount(self, items_total):
        if self.coupon:
            if self.coupon.discount_type == 'percentage':
                return items_total * (self.coupon.discount_value / 100)
            elif self.coupon.discount_type == 'fixed':
                return min(items_total, self.coupon.discount_value)
        return Decimal('0')

    def get_total(self):
        items_total = self.get_items_total()
        discount = self.apply_coupon_discount(items_total)
        return items_total - discount + (self.delivery_fee or Decimal('0'))

    # --- Status Transitions ---
    def start_processing(self):
        if self.status != self.PENDING:
            raise ValueError(f"Cannot start processing from {self.status}")
        self.status = self.PROCESSING
        self.save()

    def ship_order(self):
        if self.status != self.PROCESSING:
            raise ValueError(f"Cannot ship from {self.status}")
        self.status = self.SHIPPED
        self.save()

    def mark_out_for_delivery(self):
        if self.status != self.SHIPPED:
            raise ValueError(f"Cannot mark out for delivery from {self.status}")
        self.status = self.OUT_FOR_DELIVERY
        self.save()

    def mark_delivered(self):
        if self.status != self.OUT_FOR_DELIVERY:
            raise ValueError(f"Cannot mark delivered from {self.status}")
        self.status = self.DELIVERED
        self.save()

    def cancel(self):
        if self.status in [self.DELIVERED, self.CANCELLED]:
            raise ValueError(f"Cannot cancel an order that is {self.status}")
        self.status = self.CANCELLED
        self.save()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey("core.Product", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_subtotal(self):
        return self.price * self.quantity
