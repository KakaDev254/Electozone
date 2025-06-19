from django.urls import path
from .views import PesaPalPaymentView, pesapal_callback

urlpatterns = [
    path("pay/", PesaPalPaymentView.as_view(), name="pesapal_pay"),
    path("callback/", pesapal_callback, name="pesapal_callback"),
]