from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    is_artisan = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

class ArtisanProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to='artisan_profile', blank=True)
    location = models.CharField(max_length=120)

    def __str__(self):
        return f"ArtisanProfile of: {self.user.username}"

class BuyerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=120)
    saved_items = models.ManyToManyField('products.Product', blank=True)

    def __str__(self):
        return f"BuyerProfile of: {self.user.username}"