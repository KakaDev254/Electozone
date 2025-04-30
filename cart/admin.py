
from django.contrib import admin
from .models import Cart, CartItem ,DeliveryLocation

admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(DeliveryLocation)
