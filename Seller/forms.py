from django import forms
from django.contrib.auth.hashers import make_password
from .models import Product, Seller
from django.contrib.auth.models import User

class SellerRegistrationForm(forms.ModelForm):
    name = forms.CharField(required=True, label="Full Name")
    phone = forms.CharField(required=True, label="Phone Number")
    email = forms.EmailField(required=True)
    business_name = forms.CharField(required=True)
    address = forms.CharField(widget=forms.Textarea, required=True)
    gst_number = forms.CharField(required=True, label="GST Number")
    password = forms.CharField(widget=forms.PasswordInput)

    field_order = ['name', 'phone', 'email', 'business_name', 'address', 'gst_number', 'password']
    class Meta:
        model = Seller
        fields = ['phone', 'business_name', 'address', 'gst_number']

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['email'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['name']
        )
        seller = super().save(commit=False)
        seller.user = user
        if commit:
            seller.save()
        return seller
class SellerLoginForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'category', 'material', 'image', 'count']
