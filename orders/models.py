from django.db import models
from django.conf import settings
from core.models import Product
import logging

logger = logging.getLogger(__name__)

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
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default=PENDING)

    def __str__(self):
        return f"Order {self.id} - {self.user.email} ({self.status})"

    def get_total(self):
        return sum(item.get_subtotal() for item in self.items.all())

    def _update_status(self, new_status, allowed_from=None, reference=None):
        if allowed_from and self.status not in allowed_from:
            logger.warning(f"Invalid status transition for Order {self.id}: {self.status} -> {new_status}")
            raise ValueError(f"Cannot change status from {self.status} to {new_status}")
        self.status = new_status
        if reference:
            self.payment_reference = reference
        self.save()
        logger.info(f"Order {self.id} status updated to {self.status}")

    def mark_paid(self, reference=None):
        self._update_status(self.PAID, allowed_from=[self.PENDING], reference=reference)

    def start_processing(self):
        self._update_status(self.PROCESSING, allowed_from=[self.PAID])

    def ship_order(self):
        self._update_status(self.SHIPPED, allowed_from=[self.PROCESSING])

    def mark_out_for_delivery(self):
        self._update_status(self.OUT_FOR_DELIVERY, allowed_from=[self.SHIPPED])

    def mark_delivered(self):
        self._update_status(self.DELIVERED, allowed_from=[self.OUT_FOR_DELIVERY])

    def cancel(self):
        self._update_status(self.CANCELLED, allowed_from=[
            self.PENDING, self.PAID, self.PROCESSING, self.SHIPPED, self.OUT_FOR_DELIVERY
        ])

    def refund(self):
        self._update_status(self.REFUNDED, allowed_from=[self.PAID])

    def fail(self):
        self._update_status(self.FAILED, allowed_from=[self.PENDING])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Captures price at time of order

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_subtotal(self):
        return self.price * self.quantity
