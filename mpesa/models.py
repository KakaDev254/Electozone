
from django.db import models
from django.conf import settings
from orders.models import Order

class MpesaPayment(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    )
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='mpesa_payment', blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE , null=True, blank=True) 
    phone_number = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    mpesa_receipt_number = models.CharField(max_length=100, blank=True, null=True)
    transaction_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    # API fields
    merchant_request_id = models.CharField(max_length=100, blank=True, null=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
    response_code = models.CharField(max_length=10, blank=True, null=True)
    response_description = models.CharField(max_length=255, blank=True, null=True)
    result_code = models.CharField(max_length=10, blank=True, null=True)
    result_description = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"M-Pesa Payment for Order {self.order.id if self.order else 'N/A'}"


