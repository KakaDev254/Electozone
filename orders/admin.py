# orders/admin.py

from django.contrib import admin
from .models import Order, OrderItem

# Inline for OrderItem to display them within the Order admin page
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0  # Number of empty forms to display (0 means no empty form)

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'status', 'get_total')  # Fields to display in the list view
    list_filter = ('status', 'created_at', 'user')  # Add filters for status, created_at, and user
    search_fields = ('user__username',)  # Allow searching by username
    inlines = [OrderItemInline]  # Display OrderItems as inline forms within the Order page

    # Add a method to display the total price for the order in the list view
    def get_total(self, obj):
        return obj.get_total
    get_total.short_description = 'Total'

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')  # Fields to display in the list view
    search_fields = ('product__name',)  # Allow searching by product name

# Register the models with the admin interface
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
