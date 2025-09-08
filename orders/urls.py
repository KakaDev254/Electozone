from django.urls import path
from . import views


urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('success/<int:order_id>/', views.order_success, name='order_success'),
    
    path('change_status/<int:order_id>/<str:status>/', views.change_order_status, name='change_order_status'),
    path('order/failure/', views.order_failure, name='order_failure'),
   
   
    
]
