from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import User, ArtisanProfile

class RegisterForm(UserCreationForm):
    """
    Custom form for new user registration. Includes an option
    for users to register as an artisan.
    """
    email = forms.EmailField(required=True)
    is_artisan = forms.BooleanField(
        required=False,
        label="I want to sell my products as an Artisan",
        widget=forms.CheckboxInput(attrs={'class': 'mr-2'})
    )

    class Meta:
        model = User
        fields = ("username", "email")

class ArtisanProfileForm(forms.ModelForm):
    """
    Form for artisans to edit their main public profile information.
    This form intentionally excludes sensitive payout details.
    """
    class Meta:
        model = ArtisanProfile
        # ✅ FIX: Removed 'location' and only include the fields for this form.
        # Payout fields are handled by a separate form for security.
        fields = [
            'bio', 'profile_pic',
            'phone_number', 'address', 'city', 'state', 'postal_code'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }

class ArtisanPayoutForm(forms.ModelForm):
    """
    A separate, secure form for artisans to manage their bank details for payouts.
    """
    class Meta:
        model = ArtisanProfile
        # This form ONLY includes the sensitive payout fields.
        fields = [
            'account_holder_name', 'bank_account_number',
            'ifsc_code', 'bank_name'
        ]
        labels = {
            'account_holder_name': "Account Holder's Full Name",
            'bank_account_number': "Bank Account Number",
            'ifsc_code': "IFSC Code",
            'bank_name': "Bank Name",
        }
        help_texts = {
            'ifsc_code': "Enter the 11-character IFSC code for your bank branch."
        }
