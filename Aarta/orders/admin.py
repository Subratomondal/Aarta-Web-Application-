# Register your models here.
from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):  # Or use admin.StackedInline
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price')
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'buyer', 'full_name', 'phone_number', 'city', 'state',
        'postal_code', 'status', 'total_amount', 'created_at'
    )
    search_fields = ('buyer__username', 'full_name', 'city', 'state')
    readonly_fields = ('buyer', 'full_name', 'phone_number', 'address', 'city', 'state', 'postal_code', 'total_amount')

    inlines = [OrderItemInline]
