# payments/urls.py
from django.urls import path
from .views import PesaPalPaymentView, pesapal_callback

urlpatterns = [
    path("pay/<uuid:order_number>/", PesaPalPaymentView.as_view(), name="pesapal_pay"),
    path("callback/", pesapal_callback, name="pesapal_callback"),
]
