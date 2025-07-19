# Standard Library Imports
import json
import logging

# Third-Party Imports
import razorpay
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

# Local Application Imports
from products.models import Product
from .forms import ShippingForm, ShippingAddressForm
from .models import CartItem, Order, OrderItem, WishlistItem, ShippingAddress

# --- Initialization ---
logger = logging.getLogger(__name__)
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


# --- VIEWS START HERE ---

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        messages.error(request, "Invalid quantity.")
        return redirect('product_detail', pk=product.id)

    if quantity < 1:
        messages.error(request, "Quantity must be at least 1.")
        return redirect('product_detail', pk=product.id)

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
    insufficient_stock = any(item.quantity > item.product.stock for item in cart_items)
    total_quantity = sum(item.quantity for item in cart_items)

    return render(request, 'orders/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'insufficient_stock': insufficient_stock,
        'total_quantity': total_quantity,
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
def place_order(request):
    print(f"--- USING RAZORPAY KEY ID: {settings.RAZORPAY_KEY_ID} ---")
    cart_items = CartItem.objects.select_related('product').filter(user=request.user)
    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('view_cart')

    total_amount = sum(item.get_total_price() for item in cart_items)

    if request.method == "POST":
        use_saved = request.POST.get('use_saved')
        shipping_form = ShippingForm(request.POST)
        address_form = ShippingAddressForm(request.POST)  # This seems unused, we can review later
        shipping_data = {}

        if use_saved:
            try:
                address = ShippingAddress.objects.get(id=use_saved, user=request.user)
                shipping_data = {
                    'full_name': address.full_name, 'phone_number': address.phone_number,
                    'address': address.address, 'city': address.city,
                    'state': address.state, 'postal_code': address.postal_code
                }
            except ShippingAddress.DoesNotExist:
                messages.error(request, "Invalid saved address selected.")
                return redirect('checkout')

        elif shipping_form.is_valid():
            shipping_data = shipping_form.cleaned_data
            if request.POST.get("save_address"):
                ShippingAddress.objects.create(user=request.user, **shipping_data)

        else:
            print("--- SHIPPING FORM ERRORS ---")  # <-- DEBUGGING LINE
            print(shipping_form.errors)  # <-- DEBUGGING LINE
            messages.error(request, "Invalid shipping details.")
            return redirect('checkout')

        # This part below will only run if the shipping details are valid
        try:
            razorpay_order = razorpay_client.order.create({
                "amount": int(total_amount * 100),
                "currency": "INR",
                "receipt": f"receipt_{request.user.id}_{cart_items.count()}",
                "payment_capture": 1
            })
        except Exception as e:
            logger.error("Razorpay order creation failed: %s", str(e))
            messages.error(request, "Payment initiation failed.")
            return redirect('checkout')

        request.session['shipping_data'] = shipping_data
        request.session['razorpay_order_id'] = razorpay_order['id']

        return render(request, 'orders/payment.html', {
            "razorpay_order_id": razorpay_order['id'],
            "razorpay_key": settings.RAZORPAY_KEY_ID,
            "amount": int(total_amount * 100),
            "currency": "INR",
            "cart_items": cart_items,
            "total_amount": total_amount
        })

    return redirect('checkout')

@login_required
def payment_page(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    if not order.razorpay_order_id:
        try:
            razorpay_order = razorpay_client.order.create({
                "amount": int(order.total_amount * 100),
                "currency": "INR",
                "receipt": f"order_rcptid_{order.id}",
                "payment_capture": 1
            })
            order.razorpay_order_id = razorpay_order['id']
            order.save()
        except Exception as e:
            logger.error("Razorpay order creation failed on retry: %s", str(e))
            messages.error(request, "Could not re-initiate payment.")
            return redirect('my_orders')

    context = {
        'order': order,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'amount': int(order.total_amount * 100),
        'user': request.user
    }
    return render(request, 'orders/payment.html', context)


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
    if order.status not in ['pending', 'confirmed']:
        messages.error(request, "Only pending or confirmed orders can be canceled.")
        return redirect('my_orders')

    if request.method == "POST":
        with transaction.atomic():
            order.status = 'canceled'
            order.save()
            for item in order.items.all():
                product = item.product
                product.stock = F('stock') + item.quantity
                product.save()
        messages.success(request, "Order canceled successfully.")
        return redirect('my_orders')

    return render(request, 'orders/confirm_cancel_order.html', {'order': order})


@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
    if created:
        messages.success(request, "Added to your wishlist.")
    else:
        messages.info(request, "Already in your wishlist.")
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
    CartItem.objects.filter(user=request.user, product=product).delete()
    wishlist_item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
    if created:
        messages.success(f"{product.name} moved to your wishlist.")
    else:
        messages.info(f"{product.name} is already in your wishlist.")
    return redirect('view_cart')


@login_required
def move_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.stock <= 0:
        messages.error(f"{product.name} is out of stock and cannot be moved to cart.")
        return redirect('view_wishlist')

    WishlistItem.objects.filter(user=request.user, product=product).delete()
    cart_item, created = CartItem.objects.get_or_create(
        user=request.user, product=product,
        defaults={'quantity': 1}
    )
    if not created:
        if cart_item.quantity < product.stock:
            cart_item.quantity += 1
            cart_item.save()
        else:
            messages.error(f"Only {product.stock} of {product.name} in stock.")
            return redirect('view_wishlist')

    messages.success(f"{product.name} moved to your cart.")
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

        item.quantity = new_quantity
        item.save()
        cart_items = CartItem.objects.filter(user=request.user)
        cart_total = sum(i.get_total_price() for i in cart_items)
        total_quantity = sum(i.quantity for i in cart_items)

        return JsonResponse({
            'success': True, 'quantity': item.quantity,
            'item_total': float(item.get_total_price()),
            'cart_total': float(cart_total), 'total_quantity': total_quantity
        })
    return JsonResponse({'error': "Invalid request method."}, status=405)


@login_required
def track_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    return render(request, 'orders/track_order.html', {'order': order})


@csrf_exempt
@login_required
def verify_payment(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
        razorpay_order_id = data.get("razorpay_order_id")
        payment_id = data.get("razorpay_payment_id")
        signature = data.get("razorpay_signature")

        if not all([razorpay_order_id, payment_id, signature]):
            return JsonResponse({"error": "Missing payment info"}, status=400)

        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature,
        })

        with transaction.atomic():
            cart_items = CartItem.objects.select_related('product').filter(user=request.user).select_for_update()
            if not cart_items.exists():
                return JsonResponse({"error": "Cart is empty"}, status=400)

            total_amount = sum(item.get_total_price() for item in cart_items)
            shipping_data = request.session.get('shipping_data', {})

            order = Order.objects.create(
                buyer=request.user, total_amount=total_amount,
                payment_status='successful', status='confirmed',
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=payment_id,
                razorpay_signature=signature, **shipping_data
            )

            for item in cart_items:
                OrderItem.objects.create(
                    order=order, product=item.product,
                    quantity=item.quantity, price=item.product.price
                )
                product = item.product
                product.stock = F('stock') - item.quantity
                product.save(update_fields=['stock'])

            cart_items.delete()
            request.session.pop('shipping_data', None)
            request.session.pop('razorpay_order_id', None)

        return JsonResponse({"status": "success", "order_id": order.id})

    except razorpay.errors.SignatureVerificationError:
        return JsonResponse({"error": "Signature verification failed"}, status=400)
    except Exception as e:
        logger.error("Payment verification error: %s", str(e))
        return JsonResponse({"error": "Server error"}, status=500)


@csrf_exempt
@login_required
def api_cancel_pending_payment(request, order_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    if order.payment_status == "initiated":
        order.payment_status = "failed"
        order.status = "canceled"
        order.save()
        return JsonResponse({"status": "canceled"})

    return JsonResponse({"status": "not_cancellable"}, status=400)