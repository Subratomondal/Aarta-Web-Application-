import os
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator

from users.models import ArtisanProfile, User


class Category(models.Model):
    name = models.CharField(max_length=100)
    is_featured = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Product(models.Model):
    artisan = models.ForeignKey(ArtisanProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=100) # This can be the artisan's location
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_featured = models.BooleanField(default=False)

    # --- NEW LOGISTICS FIELDS ---
    # These fields store the dimensions and weight of the FINAL PACKAGED item.
    weight_in_grams = models.PositiveIntegerField(
        default=500,
        help_text="Weight of the packaged item in grams (e.g., 500 for 0.5 kg)"
    )
    length_in_cm = models.DecimalField(
        max_digits=6, decimal_places=2, default=10.00,
        help_text="Length of the package in centimeters"
    )
    width_in_cm = models.DecimalField(
        max_digits=6, decimal_places=2, default=10.00,
        help_text="Width of the package in centimeters"
    )
    height_in_cm = models.DecimalField(
        max_digits=6, decimal_places=2, default=10.00,
        help_text="Height of the package in centimeters"
    )
    # ---------------------------

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image_path = models.ImageField(upload_to='product_images/')

    def __str__(self):
        return f"Image for {self.product.name}"


class Review(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)] # Added validators
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.buyer.username} on {self.product.name}"


@receiver(post_delete, sender=ProductImage)
def delete_image_file(sender, instance, **kwargs):
    """
    Deletes the image file from storage when the ProductImage instance is deleted.
    """
    if instance.image_path and os.path.isfile(instance.image_path.path):
        try:
            os.remove(instance.image_path.path)
        except Exception as e:
            # Using a logger is better for production
            print(f"Error deleting file: {e}")