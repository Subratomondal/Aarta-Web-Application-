from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_artisan = models.BooleanField(default=False)
    is_approved_artisan = models.BooleanField(default=False)  # ✅ New field
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

    def delete(self, *args, **kwargs):
        # Ensure related profile is deleted
        if self.is_artisan and hasattr(self, 'artisanprofile'):
            self.artisanprofile.delete()
        elif hasattr(self, 'buyerprofile'):
            self.buyerprofile.delete()
        super().delete(*args, **kwargs)


class ArtisanProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to='artisan_profile', blank=True)

    location = models.CharField(max_length=120)

    # Additional Fields
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"ArtisanProfile of: {self.user.username}"


class BuyerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=120)
    saved_items = models.ManyToManyField('products.Product', blank=True)

    def __str__(self):
        return f"BuyerProfile of: {self.user.username}"
