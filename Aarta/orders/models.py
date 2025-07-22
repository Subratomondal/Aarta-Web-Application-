from django.db import models
from products.models import Product
from users.models import User


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
    ]

    buyer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)

    # --- NEW & UPDATED COST FIELDS ---
    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        help_text="The total cost of all items before shipping and taxes."
    )
    shipping_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        help_text="The final, calculated shipping cost for this order."
    )
    # The existing 'total_amount' will now represent the Grand Total
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="The grand total of the order (subtotal + shipping + taxes)."
    )
    # ------------------------------------

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Shipping Info (copied for historical record)
    full_name = models.CharField(max_length=100, default="Unnamed")
    phone_number = models.CharField(max_length=15, default="0000000000")
    address = models.TextField(default="Default Address")
    city = models.CharField(max_length=50, default="City")
    state = models.CharField(max_length=50, default="State")
    postal_code = models.CharField(max_length=10, default="000000")

    # Razorpay Payment Info
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='initiated')

    def __str__(self):
        return f"Order #{self.id} by {self.buyer.username if self.buyer else 'Guest'}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price of the item at the time of purchase.")

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order #{self.order.id})"


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in {self.user.username}'s cart"

    def get_total_price(self):
        return self.quantity * self.product.price


class WishlistItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} → {self.product.name}"


class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipping_addresses')
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name}, {self.city}, {self.state}"
