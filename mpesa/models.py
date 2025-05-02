from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from orders.models import Order

class MpesaPayment(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    )

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='mpesa_payment',
        blank=True,
        null=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    phone_number = models.CharField(
        max_length=20,
        validators=[RegexValidator(regex=r'^\+?254\d{9}$', message="Enter a valid Kenyan phone number.")]
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    mpesa_receipt_number = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True
    )
    transaction_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    # M-Pesa API metadata
    merchant_request_id = models.CharField(max_length=100, blank=True, null=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
    response_code = models.CharField(max_length=10, blank=True, null=True)
    response_description = models.CharField(max_length=255, blank=True, null=True)
    result_code = models.CharField(max_length=10, blank=True, null=True)
    result_description = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.mpesa_receipt_number:
            return f"M-Pesa Payment: {self.mpesa_receipt_number}"
        elif self.order:
            return f"M-Pesa Payment for Order {self.order.id}"
        else:
            return "M-Pesa Payment (No Reference)"
