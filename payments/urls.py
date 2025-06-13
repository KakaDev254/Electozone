from django.urls import path
from . import views

urlpatterns = [
    path('pay/<int:order_id>/', views.initiate_payment, name='initiate_payment'),
    path('callback/', views.payment_callback, name='payment_callback'),
    path("payments/ipn/", views.pesapal_ipn_listener, name="pesapal_ipn_listener")
]