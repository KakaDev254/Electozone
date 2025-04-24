from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.products_list, name='products'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('search/', views.product_search, name='product_search'),
    


]