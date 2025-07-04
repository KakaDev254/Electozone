from django.urls import path
from .views import PesaPalPaymentView, pesapal_callback, pesapal_ipn_listener

urlpatterns = [
    path("pay/<uuid:order_number>/", PesaPalPaymentView.as_view(), name="pesapal_pay"),
    path("callback/", pesapal_callback, name="pesapal_callback"),
    path("ipn/", pesapal_ipn_listener, name="pesapal_ipn"),  # 👈 NEW
]
