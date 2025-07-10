from django.contrib import admin
from .models import Product, Category, ProductImage

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'artisan', 'price', 'stock', 'is_approved')
    list_filter = ('is_approved', 'category')
    actions = ['approve_selected']

    @admin.action(description='Approve selected products')
    def approve_selected(self, request, queryset):
        queryset.update(is_approved=True)

admin.site.register(Category)
admin.site.register(ProductImage)
