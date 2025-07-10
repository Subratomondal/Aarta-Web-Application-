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
    return render(request, 'orders/cart.html', {'cart_items': cart_items, 'total': total})


@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.delete()
    messages.info(request, "Item removed from cart.")
    return redirect('view_cart')


@login_required
def place_order(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items:
        messages.error(request, "Your cart is empty.")
        return redirect('view_cart')

    total = sum(item.get_total_price() for item in cart_items)

    order = Order.objects.create(buyer=request.user, total_amount=total)
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price,
        )
        # Reduce stock
        item.product.stock -= item.quantity
        item.product.save()

    cart_items.delete()
    messages.success(request, "Order placed successfully!")

    # 🔽 Redirect to success page after order
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