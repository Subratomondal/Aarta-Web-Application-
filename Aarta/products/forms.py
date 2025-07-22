from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        # ✅ Updated the fields to include weight and dimensions
        fields = [
            'name', 'description', 'price', 'stock', 'category', 'location',
            'weight_in_grams', 'length_in_cm', 'width_in_cm', 'height_in_cm'
        ]
        # Optional: Add help texts to the form fields for clarity
        help_texts = {
            'weight_in_grams': 'Enter the total weight of the item *after* it is packaged, in grams.',
            'length_in_cm': 'Enter the longest side of the package in centimeters.',
            'width_in_cm': 'Enter the second longest side of the package in centimeters.',
            'height_in_cm': 'Enter the shortest side of the package in centimeters.',
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        if self.request:
            new_images = self.request.FILES.getlist('images')
            existing_image_count = self.instance.images.count() if self.instance.pk else 0
            total_images = existing_image_count + len(new_images)

            if total_images > 4:
                raise forms.ValidationError("You can only upload a total of 4 images per product.")

        return cleaned_data
