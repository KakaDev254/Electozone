from django.urls import path
from .views import *


urlpatterns = [
    path('stk-push/', initiate_stk_push, name='stk_push'),
     path('mpesa/callback/', mpesa_callback, name='mpesa_callback'),
    path('pay/', payment_page, name='payment_page'),
    path('check_payment_status/', check_payment_status, name='payment_status'),


]
