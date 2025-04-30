# mpesa_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('initiate-payment/<int:order_id>/', views.initiate_payment, name='initiate_payment'),
    path('mpesa-callback/', views.mpesa_callback, name='mpesa_callback'),
    path('check-payment-status/<str:merchant_request_id>/', views.check_payment_status, name='check_payment_status'),
    path('payment-success/<int:order_id>/', views.payment_success, name='payment_success'),
    path('cancel-payment/<int:order_id>/', views.cancel_payment, name='cancel_payment'),
]
