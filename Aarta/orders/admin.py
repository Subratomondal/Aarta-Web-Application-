# Register your models here.
from django.contrib import admin
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'buyer', 'full_name', 'phone_number', 'city', 'state',
        'postal_code', 'status', 'total_amount', 'created_at','address'
    )
    search_fields = ('buyer__username', 'full_name', 'city', 'state')
    readonly_fields = ('buyer', 'full_name', 'phone_number', 'address', 'city', 'state', 'postal_code', 'total_amount')