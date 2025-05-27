from django import forms
from .models import CustomUser

class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'second_name','email', 'phone_number', 'address', 'city', 'postal_code']