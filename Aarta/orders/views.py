from django.db import transaction
from django.db.models import F
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .forms import ShippingForm, ShippingAddressForm
from .models import CartItem, Order, OrderItem, WishlistItem, ShippingAddress
from products.models import Product
from django.contrib import messages
from django.http import JsonResponse

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

    # ✅ Add total_quantity here
    total_quantity = sum(item.quantity for item in cart_items)

    return render(request, 'orders/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'insufficient_stock': insufficient_stock,
        'total_quantity': total_quantity,  # ✅ Add this
    })

@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.delete()
    messages.info(request, "Item removed from cart.")
    return redirect('view_cart')


@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items:
        messages.error(request, "Your cart is empty.")
        return redirect('view_cart')

    total = sum(item.get_total_price() for item in cart_items)

    saved_addresses = ShippingAddress.objects.filter(user=request.user)
    shipping_form = ShippingForm()
    address_form = ShippingAddressForm()

    return render(request, 'orders/checkout.html', {
        'cart_items': cart_items,
        'total': total,
        'shipping_form': shipping_form,
        'address_form': address_form,
        'saved_addresses': saved_addresses
    })

@login_required
@transaction.atomic
def place_order(request):
    cart_items = CartItem.objects.select_related('product').filter(user=request.user).select_for_update()
    if not cart_items:
        messages.error(request, "Your cart is empty.")
        return redirect('view_cart')

    total = sum(item.get_total_price() for item in cart_items)

    if request.method == "POST":
        use_saved = request.POST.get('use_saved')
        shipping_form = ShippingForm(request.POST)
        address_form = ShippingAddressForm(request.POST)

        if use_saved:
            try:
                address = ShippingAddress.objects.get(id=use_saved, user=request.user)
                order = Order.objects.create(
                    buyer=request.user,
                    total_amount=total,
                    full_name=address.full_name,
                    phone_number=address.phone_number,
                    address=address.address,
                    city=address.city,
                    state=address.state,
                    postal_code=address.postal_code
                )
            except ShippingAddress.DoesNotExist:
                messages.error(request, "Invalid saved address selected.")
                return redirect('checkout')
        elif shipping_form.is_valid():
            order = shipping_form.save(commit=False)
            order.buyer = request.user
            order.total_amount = total
            order.save()

            # Optionally save this address for future use
            if request.POST.get("save_address"):
                ShippingAddress.objects.create(
                    user=request.user,
                    full_name=order.full_name,
                    phone_number=order.phone_number,
                    address=order.address,
                    city=order.city,
                    state=order.state,
                    postal_code=order.postal_code
                )
        else:
            messages.error(request, "Please fill out a valid shipping address.")
            return redirect('checkout')

        for item in cart_items:
            if item.quantity > item.product.stock:
                messages.error(request, f"Not enough stock for {item.product.name}")
                return redirect('view_cart')

            item.product.stock = F('stock') - item.quantity
            item.product.save()

            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

        cart_items.delete()
        messages.success(request, "Order placed successfully!")
        return redirect('order_success', order_id=order.id)

    return redirect('checkout')

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    return render(request, 'orders/order_success.html', {'order': order})

@login_required
def saved_addresses(request):
    addresses = ShippingAddress.objects.filter(user=request.user)
    return render(request, 'orders/saved_addresses.html', {'addresses': addresses})

@login_required
def my_orders(request):
    orders = Order.objects.filter(buyer=request.user).order_by('-created_at')
    return render(request, 'orders/my_orders.html', {'orders': orders})

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)

    if order.status != 'pending':
        messages.error(request, "Only pending orders can be canceled.")
        return redirect('my_orders')

    if request.method == "POST":
        # Mark order as canceled
        order.status = 'canceled'
        order.save()

        # Restore product stock
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()

        messages.success(request, "Order canceled successfully.")
        return redirect('my_orders')

    return render(request, 'orders/confirm_cancel_order.html', {'order': order})



@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)

    if not created:
        messages.info(request, "Already in your wishlist.")
    else:
        messages.success(request, "Added to your wishlist.")

    return redirect('product_detail', pk=product_id)

@login_required
def remove_from_wishlist(request, product_id):
    WishlistItem.objects.filter(user=request.user, product_id=product_id).delete()
    messages.success(request, "Removed from wishlist.")
    return redirect('view_wishlist')

@login_required
def view_wishlist(request):
    wishlist_items = WishlistItem.objects.filter(user=request.user)
    return render(request, 'orders/wishlist.html', {'wishlist_items': wishlist_items})

@login_required
def move_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Delete the product from cart if it exists
    CartItem.objects.filter(user=request.user, product=product).delete()

    # Add to wishlist (if not already present)
    wishlist_item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)

    if created:
        messages.success(request, f"{product.name} moved to your wishlist.")
    else:
        messages.info(request, f"{product.name} is already in your wishlist.")

    return redirect('view_cart')


@login_required
def move_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Remove from wishlist if it exists
    WishlistItem.objects.filter(user=request.user, product=product).delete()

    # Add to cart if not already there
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    else:
        cart_item.quantity = 1
        cart_item.save()

    messages.success(request, f"{product.name} moved to your cart.")
    return redirect('view_wishlist')

@login_required
def update_cart_quantity(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)

    if request.method == "POST":
        try:
            new_quantity = int(request.POST.get('quantity'))
        except (ValueError, TypeError):
            return JsonResponse({'error': "Invalid quantity."}, status=400)

        if new_quantity < 1:
            item.delete()
            return JsonResponse({'removed': True})
        elif new_quantity > item.product.stock:
            return JsonResponse({'error': f"Only {item.product.stock} in stock."}, status=400)
        else:
            item.quantity = new_quantity
            item.save()

            cart_items = CartItem.objects.filter(user=request.user)
            cart_total = sum(i.get_total_price() for i in cart_items)
            total_quantity = sum(i.quantity for i in cart_items)

            return JsonResponse({
                'success': True,
                'quantity': item.quantity,
                'item_total': float(item.get_total_price()),
                'cart_total': float(cart_total),
                'total_quantity': total_quantity
            })

    return JsonResponse({'error': "Invalid request method."}, status=405)


@login_required
def track_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    steps = ['processing', 'shipped', 'delivered']
    return render(request, 'orders/track_order.html', {
        'order': order,
        'steps': steps  # ✅ pass this to the template
    })