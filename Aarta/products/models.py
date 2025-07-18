
from django.db import models

from users.models import ArtisanProfile, User


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100)
    is_featured = models.BooleanField(default=False)  # 👈 Admin-controlled
    def __str__(self):
        return self.name


class Product(models.Model):
    artisan = models.ForeignKey(ArtisanProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    location = models.CharField(max_length=100)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_featured = models.BooleanField(default=False)
    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image_path = models.ImageField(upload_to='product_images/')

    def __str__(self):
        return f"Image for {self.product.name}"



class Review(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.buyer.username} on {self.product.name}"



import os
from django.db.models.signals import post_delete
from django.dispatch import receiver

@receiver(post_delete, sender=ProductImage)
def delete_image_file(sender, instance, **kwargs):
    """
    Deletes the image file from storage when the ProductImage instance is deleted.
    """
    if instance.image_path and os.path.isfile(instance.image_path.path):
        try:
            os.remove(instance.image_path.path)
        except Exception as e:
            print(f"Error deleting file: {e}")