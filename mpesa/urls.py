from django.urls import path
from . import views

urlpatterns = [
    path('pay/', views.payment_page, name='payment_page'),
    path('stk-push/', views.stk_push_request, name='stk_push'),
    path('payment-status/', views.payment_status, name='payment_status'),
    path('callback/', views.mpesa_callback, name='mpesa_callback'),
]

