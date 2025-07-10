from django import forms

from products.models import Product, ProductImage


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name','description','price','stock','category','location']


