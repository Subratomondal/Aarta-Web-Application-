from django.contrib import admin
from .models import Order, OrderItem
from products.models import Product  # Adjust if needed

class OrderItemInline(admin.TabularInline):
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

    def save_model(self, request, obj, form, change):
        if change:
            previous = Order.objects.get(pk=obj.pk)
            if previous.status != 'canceled' and obj.status == 'canceled':
                # Restore stock for all items in this order
                for item in obj.items.all():
                    item.product.stock += item.quantity
                    item.product.save()
        super().save_model(request, obj, form, change)
