from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('female_toys', 'Female Toys'),
        ('male_toys', 'Male Toys'),
        ('dildos', 'Dildos'),
        ('vibrators', 'Vibrators'),
        ('bondage_kits', 'Bondage Kits'),
        ('anal_toys', 'Anal_toys'),
        ('adult_games', 'Aduilt Games'),
        ('lubes', 'Lubes'),
        ('condoms', 'Condoms'),
    ]

    name = models.CharField(max_length=100)
    price = models.IntegerField()
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
    
   


