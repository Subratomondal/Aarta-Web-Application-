from django.contrib import admin
from .models import Product, Category, ProductImage

# Define an Inline for ProductImage
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # How many extra empty forms to show

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'artisan', 'price', 'stock', 'is_approved', 'is_featured')
    list_filter = ('is_approved', 'is_featured', 'category')
    search_fields = ('name', 'artisan__user__username') # Added for easier searching
    actions = ['approve_selected', 'mark_as_featured', 'remove_from_featured']
    inlines = [ProductImageInline] # Add the inline here

    @admin.action(description='Approve selected products')
    def approve_selected(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description='Mark selected products as Featured')
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description='Remove selected products from Featured')
    def remove_from_featured(self, request, queryset):
        queryset.update(is_featured=False)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_featured')
    list_editable = ('is_featured',)
    list_filter = ('is_featured',)

