# orders/models.py

from django.db import models
from django.conf import settings
from core.models import Product

class Order(models.Model):
    PENDING = 'pending'
    PAID = 'paid'
    PROCESSING = 'processing'
    SHIPPED = 'shipped'
    OUT_FOR_DELIVERY = 'out_for_delivery'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'
    FAILED = 'failed'

    ORDER_STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PAID, 'Paid'),
        (PROCESSING, 'Processing'),
        (SHIPPED, 'Shipped'),
        (OUT_FOR_DELIVERY, 'Out for Delivery'),
        (DELIVERED, 'Delivered'),
        (CANCELLED, 'Cancelled'),
        (REFUNDED, 'Refunded'),
        (FAILED, 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default=PENDING,
    )

    def __str__(self):
        return f"Order {self.id} by {self.user.email}"

    @property
    def get_total(self):
        return sum(item.get_subtotal() for item in self.items.all())

    def mark_paid(self):
        if self.status == self.PENDING:
            self.status = self.PAID
            self.save()

    def start_processing(self):
        if self.status == self.PAID:
            self.status = self.PROCESSING
            self.save()

    def ship_order(self):
        if self.status == self.PROCESSING:
            self.status = self.SHIPPED
            self.save()

    def out_for_delivery(self):
        if self.status == self.SHIPPED:
            self.status = self.OUT_FOR_DELIVERY
            self.save()

    def deliver(self):
        if self.status == self.OUT_FOR_DELIVERY:
            self.status = self.DELIVERED
            self.save()

    def cancel(self):
        if self.status not in [self.DELIVERED, self.REFUNDED]:
            self.status = self.CANCELLED
            self.save()

    def refund(self):
        if self.status == self.PAID:
            self.status = self.REFUNDED
            self.save()

    def fail(self):
        if self.status == self.PENDING:
            self.status = self.FAILED
            self.save()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Saved copy of price

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_subtotal(self):
        return self.price * self.quantity
