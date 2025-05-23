

from django.urls import path
from . import views

urlpatterns = [
    path('', views.view_cart, name='view_cart'),
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'), 
    path('remove-coupon/', views.remove_coupon, name='remove_coupon'),
    path("set-delivery-location/", views.set_delivery_location, name="set_delivery_location"),

]
