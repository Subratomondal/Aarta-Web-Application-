from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Adds flags for managing artisan roles and approval status.
    """
    is_artisan = models.BooleanField(default=False)
    is_approved_artisan = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class ArtisanProfile(models.Model):
    """
    Stores all profile-specific information for an artisan user,
    including their bio, location, and secure payout details.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    profile_pic = models.ImageField(upload_to='artisan_profile/', blank=True, null=True)

    # --- Contact & Location Information ---
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)

    # --- Payout Information ---
    # These fields are for admin use to process payouts to the artisan.
    account_holder_name = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Full name as it appears on the bank account."
    )
    bank_account_number = models.CharField(
        max_length=20, blank=True, null=True,
        help_text="Your complete bank account number."
    )
    ifsc_code = models.CharField(
        max_length=11, blank=True, null=True,
        help_text="The 11-character IFSC code of your bank branch."
    )
    bank_name = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="The name of your bank (e.g., State Bank of India)."
    )

    def __str__(self):
        return f"ArtisanProfile of: {self.user.username}"


class BuyerProfile(models.Model):
    """
    Stores profile-specific information for a buyer user.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=120, blank=True, null=True)

    def __str__(self):
        return f"BuyerProfile of: {self.user.username}"
