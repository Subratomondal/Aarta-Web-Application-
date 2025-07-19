from django.contrib.auth.forms import UserCreationForm
from django import forms
from users.models import User, ArtisanProfile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    is_artisan = forms.BooleanField(
        required=False,
        label="I want to sell my products as an Artisan",
        widget=forms.CheckboxInput(attrs={'class': 'mr-2'})
    )

    class Meta:
        model = User
        # ✅ Simplified to only include the model fields.
        # The form automatically handles password fields.
        fields = ("username", "email")

# ... your ArtisanProfileForm would go here ...

class ArtisanProfileForm(forms.ModelForm):
    class Meta:
        model = ArtisanProfile
        fields = [
            'bio', 'profile_pic', 'location',
            'phone_number', 'address', 'city', 'state', 'postal_code'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'w-full'}),
            'profile_pic': forms.FileInput(),
            'location': forms.TextInput(attrs={'class': 'w-full'}),
            'phone_number': forms.TextInput(attrs={'class': 'w-full'}),
            'address': forms.Textarea(attrs={'class': 'w-full', 'rows': 2}),
            'city': forms.TextInput(attrs={'class': 'w-full'}),
            'state': forms.TextInput(attrs={'class': 'w-full'}),
            'postal_code': forms.TextInput(attrs={'class': 'w-full'}),
        }




