from django.db import models
from django.conf import settings
from core.models import Product
from decimal import Decimal
import logging
import uuid

logger = logging.getLogger(__name__)

class Order(models.Model):
    # --- Status Constants ---
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

    # --- Core Order Info ---
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    order_number = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default=PENDING)

    # --- Address Fields ---
    address = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)

    # --- Payment & Delivery ---
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    pesapal_tracking_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
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

    def mark_paid_with_tracking(self, reference=None, tracking_id=None):
        if tracking_id:
            if Order.objects.exclude(id=self.id).filter(pesapal_tracking_id=tracking_id).exists():
                logger.warning(f"Duplicate tracking ID for Order {self.id}: {tracking_id}")
                raise ValueError("Tracking ID already used for another order")
            self.pesapal_tracking_id = tracking_id
        self.mark_paid(reference=reference)

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
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_subtotal(self):
        return self.price * self.quantity
