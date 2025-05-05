from django.db import models

class Payment(models.Model):
    phone = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    checkout_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, default='pending')  # pending, success, failed, cancelled, timeout
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone} - {self.status} ({self.amount})"
