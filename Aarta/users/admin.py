from django.contrib import admin
from .models import ArtisanProfile

@admin.register(ArtisanProfile)
class ArtisanAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'city', 'postal_code','state']
    search_fields = ['user__username', 'city', 'state']

