# In core/admin.py

from django.contrib import admin
from .models import ShippingRate

@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = ('weight_slab_grams', 'regional_rate', 'national_rate')
    list_editable = ('regional_rate', 'national_rate')
    search_fields = ('weight_slab_grams',)