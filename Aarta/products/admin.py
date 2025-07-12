from django.contrib import admin
from .models import Product, Category, ProductImage

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'artisan', 'price', 'stock', 'is_approved','is_featured')
    list_filter = ('is_approved','is_featured', 'category')
    actions = ['approve_selected','mark_as_featured', 'remove_from_featured']

    @admin.action(description='Approve selected products')
    def approve_selected(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description='Mark selected products as Featured')
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description='Remove selected products from Featured')
    def remove_from_featured(self, request, queryset):
        queryset.update(is_featured=False)

admin.site.register(Category)
admin.site.register(ProductImage)
