from django.db import models
from django.conf import settings


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('smartphones', 'Smartphones'),
        ('laptops', 'Laptops'),
        ('accessories', 'Accessories'),
        ('smartwatches', 'Smartwatches'),
        ('gaming', 'Gaming'),
        ('others', 'Others'),
    ]

    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    main_image = models.ImageField(upload_to='products/')
    image_1 = models.ImageField(upload_to='products/', blank=True, null=True)
    image_2 = models.ImageField(upload_to='products/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='products/', blank=True, null=True)
    image_4 = models.ImageField(upload_to='products/', blank=True, null=True)
    spec_1 = models.CharField(max_length=255, blank=True, null=True)
    spec_2 = models.CharField(max_length=255, blank=True, null=True)
    spec_3 = models.CharField(max_length=255, blank=True, null=True)
    spec_4 = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    is_featured = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
   


