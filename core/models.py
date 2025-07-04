from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField
from django.utils import timezone


class Category(models.Model):
    slug = models.SlugField(unique=True)  # e.g., 'vibrators'
    name = models.CharField(max_length=50)  # e.g., 'Vibrators'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    main_image = CloudinaryField('image')
    image_1 = CloudinaryField('image', blank=True, null=True)
    image_2 = CloudinaryField('image', blank=True, null=True)
    image_3 = CloudinaryField('image', blank=True, null=True)
    image_4 = CloudinaryField('image', blank=True, null=True)

    spec_1 = models.CharField(max_length=255, blank=True, null=True)
    spec_2 = models.CharField(max_length=255, blank=True, null=True)
    spec_3 = models.CharField(max_length=255, blank=True, null=True)
    spec_4 = models.CharField(max_length=255, blank=True, null=True)

    # 🔁 NEW: ManyToManyField for multiple categories
    categories = models.ManyToManyField(Category, related_name='products')

    is_featured = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name
    
   


