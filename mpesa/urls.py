from django.urls import path
from .views import *


urlpatterns = [
    path('stk-push/', initiate_stk_push, name='stk_push'),
    path('callback/', mpesa_callback, name='mpesa_callback'),
    path('pay/', payment_page, name='payment_page'),


]
