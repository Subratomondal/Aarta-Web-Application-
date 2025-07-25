from django.db import models
from django.core.validators import MinValueValidator

class ShippingRate(models.Model):
    """
    Stores the shipping rate card based on weight slabs and simplified zones.
    This allows an admin to manage shipping costs from the Django admin panel.
    """
    weight_slab_grams = models.PositiveIntegerField(
        unique=True,
        help_text="The upper weight limit for this slab in grams (e.g., 500 for 0-500g)."
    )
    regional_rate = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)],
        help_text="Cost for local/regional shipping (e.g., average of Zone A & B).",
        default=0.00 # ✅ ADD THIS
    )
    metro_rate = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)],
        help_text="Cost for shipping between metro cities (e.g., average of Zone C).",
        default=0.00 # ✅ ADD THIS
    )
    national_rate = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)],
        help_text="Cost for shipping to the rest of India (e.g., average of Zone D).",
        default=0.00 # ✅ ADD THIS
    )

    class Meta:
        ordering = ['weight_slab_grams']

    def __str__(self):
        return f"Up to {self.weight_slab_grams}g Rates"