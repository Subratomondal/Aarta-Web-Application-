from django.db import models
from django.core.validators import MinValueValidator

class ShippingRate(models.Model):
    """
    Stores the shipping rate card based on weight slabs.
    This allows an admin to manage shipping costs from the Django admin panel.
    """
    weight_slab_grams = models.PositiveIntegerField(
        unique=True,
        help_text="The upper limit for this weight slab in grams (e.g., 500 for 0-500g)."
    )
    regional_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.0)],
        help_text="Shipping cost for within the artisan's state/region."
    )
    national_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.0)],
        help_text="Shipping cost for the rest of India."
    )

    class Meta:
        ordering = ['weight_slab_grams'] # Always show rates from lightest to heaviest

    def __str__(self):
        return f"Up to {self.weight_slab_grams}g: Regional ₹{self.regional_rate}, National ₹{self.national_rate}"
