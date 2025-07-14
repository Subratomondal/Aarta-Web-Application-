from django.db import transaction
from django.db.models import F
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CartItem, Order, OrderItem
from products.models import Product
from django.contrib import messages


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Get quantity from POST request or default to 1
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        messages.error(request, "Invalid quantity.")
        return redirect('product_detail', pk=product.id)


    if quantity < 1:
        messages.error(request, "Quantity must be at least 1.")
        return redirect('product_detail', pk=product.id)

    # Check stock limit
    existing_item = CartItem.objects.filter(user=request.user, product=product).first()
    total_quantity = quantity
    if existing_item:
        total_quantity += existing_item.quantity

    if total_quantity > product.stock:
        messages.error(request, f"Only {product.stock} items available in stock.")
        return redirect('product_detail', pk=product.id)

    if existing_item:
        existing_item.quantity += quantity
        existing_item.save()
    else:
        CartItem.objects.create(user=request.user, product=product, quantity=quantity)

    messages.success(request, f"{product.name} added to cart.")
    return redirect('view_cart')


@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.get_total_price() for item in cart_items)

    # Check if any cart item exceeds available stock
    insufficient_stock = any(item.quantity > item.product.stock for item in cart_items)

    return render(request, 'orders/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'insufficient_stock': insufficient_stock
    })

@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.delete()
    messages.info(request, "Item removed from cart.")
    return redirect('view_cart')


@login_required
@transaction.atomic
def place_order(request):
    cart_items = CartItem.objects.select_related('product').filter(user=request.user).select_for_update()

    if not cart_items:
        messages.error(request, "Your cart is empty.")
        return redirect('view_cart')

    # Validate stock availability
    for item in cart_items:
        if item.quantity > item.product.stock:
            messages.error(request, f"Only {item.product.stock} unit(s) left for '{item.product.name}'. Please update your cart.")
            return redirect('view_cart')

    # Create Order
    total = sum(item.get_total_price() for item in cart_items)
    order = Order.objects.create(buyer=request.user, total_amount=total)

    # Deduct stock and create OrderItems
    for item in cart_items:
        product = item.product
        product.stock = F('stock') - item.quantity
        product.save()

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=item.quantity,
            price=product.price
        )

    cart_items.delete()
    messages.success(request, "Order placed successfully!")

    return redirect('order_success', order_id=order.id)

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    return render(request, 'orders/order_success.html', {'order': order})

@login_required
def my_orders(request):
    orders = Order.objects.filter(buyer=request.user).order_by('-created_at')
    return render(request, 'orders/my_orders.html', {'orders': orders})

@login_required
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Only the user who placed the order can delete it
    if order.buyer != request.user:
        return HttpResponseForbidden("You are not allowed to delete this order.")

    if request.method == "POST":
        # Restore stock before deleting the order
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()

        order.delete()
        messages.success(request, "Order deleted successfully.")
        return redirect('my_orders')

    return render(request, 'orders/confirm_delete_order.html', {'order': order})