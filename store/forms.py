from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from store.models import Order, User


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control mb-2',
        'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control mb-3',
        'placeholder': 'Password'
    }))


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User  # Tell the form to use your CustomUser model
        # Fields to include on the registration form.
        # UserCreationForm by default includes username and password fields.
        # If your CustomUser requires email, first_name, last_name, add them here.
        # For CustomUser inheriting AbstractUser, 'email' is often a good addition.
        fields = UserCreationForm.Meta.fields + ('phone_number', 'address', 'city', 'postal_code', 'country')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control mb-2'
            if field_name not in ['password', 'password2']:  # Keep default placeholders for password
                field.widget.attrs['placeholder'] = field.label or field_name.replace('_', ' ').title()


class OrderAddressForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['address', 'city', 'postal_code', 'country']
        widgets = {
            'address': forms.TextInput(attrs={'class': 'form-control mb-2', 'placeholder': 'Address'}),
            'city': forms.TextInput(attrs={'class': 'form-control mb-2', 'placeholder': 'City'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control mb-2', 'placeholder': 'Postal Code'}),
            'country': forms.TextInput(attrs={'class': 'form-control mb-2', 'placeholder': 'Country'}),
        }
