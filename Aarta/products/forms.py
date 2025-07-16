from django import forms
from products.models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'category', 'location']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # Extract request
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        if self.request:
            new_images = self.request.FILES.getlist('images')

            # When editing: count current images. When adding: count = 0
            existing_image_count = self.instance.images.count() if self.instance.pk else 0
            total_images = existing_image_count + len(new_images)

            if total_images > 4:
                raise forms.ValidationError("You can only upload a total of 4 images per product.")

        return cleaned_data

