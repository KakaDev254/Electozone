from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["address", "city", "postal_code", "phone_number"]  # ✅ only delivery details
        widgets = {
            "address": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter your address"
            }),
            "city": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter your city"
            }),
            "postal_code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter postal code"
            }),
            "phone_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter your phone number"
            }),
        }

