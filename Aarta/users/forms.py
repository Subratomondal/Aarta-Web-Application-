from django.contrib.auth.forms import UserCreationForm
from django import forms
from users.models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    is_artisan = forms.BooleanField(
        required=False,
        label="I want to sell my products as an Artisan",
        widget=forms.CheckboxInput(attrs={'class': 'mr-2'})
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2", "is_artisan"]
