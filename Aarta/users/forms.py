from django.contrib.auth.forms import UserCreationForm

from django.forms import EmailField
from users.models import User


class RegisterForm(UserCreationForm):
    email = EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2",'is_artisan']