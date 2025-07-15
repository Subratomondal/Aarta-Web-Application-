from django import forms
from .models import Order, ShippingAddress


class ShippingForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['full_name', 'phone_number', 'address', 'city', 'state', 'postal_code']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.initial = ''
            field.widget.attrs['placeholder'] = f"Enter {field.label.lower()}"
            field.widget.attrs['class'] = (
                "w-full mt-1 border border-brown/30 px-4 py-2 rounded-md "
                "focus:ring-brown focus:border-brown"
            )


class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        exclude = ['user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs['placeholder'] = f"Enter {field.label.lower()}"
            field.widget.attrs['class'] = (
                "w-full mt-1 border border-brown/30 px-4 py-2 rounded-md "
                "focus:ring-brown focus:border-brown"
            )
