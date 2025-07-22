# Standard Library Imports
import json
import logging
from collections import defaultdict
from decimal import Decimal

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

from core.models import ShippingRate
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
    cart_items = CartItem.objects.filter(user=request.user).select_related('product', 'product__artisan')

    subtotal = Decimal('0.00')
    estimated_shipping = Decimal('0.00')

    # --- NEW COMBINED SHIPPING LOGIC ---

    # Step 1: Group items and their total weights by artisan
    artisan_packages = defaultdict(lambda: {'total_weight': 0, 'items': []})
    for item in cart_items:
        subtotal += item.get_total_price()
        artisan_id = item.product.artisan.id
        artisan_packages[artisan_id]['items'].append(item)
        artisan_packages[artisan_id]['total_weight'] += item.product.weight_in_grams * item.quantity

    # Step 2: Calculate shipping for each artisan's package
    shipping_rates = ShippingRate.objects.all()
    for artisan_id, package_data in artisan_packages.items():
        total_weight = package_data['total_weight']
        package_shipping_cost = Decimal('0.00')

        # Find the correct shipping rate for the total weight of this package
        for rate in shipping_rates:
            if total_weight <= rate.weight_slab_grams:
                # Use the regional rate for estimation in the cart
                package_shipping_cost = rate.regional_rate
                break

        # If a package is heavier than any slab, we might need a fallback.
        # For now, we'll assume it falls into one.
        estimated_shipping += package_shipping_cost

    # --- END OF NEW LOGIC ---

    grand_total = subtotal + estimated_shipping
    insufficient_stock = any(item.quantity > item.product.stock for item in cart_items)
    total_quantity = sum(item.quantity for item in cart_items)

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'estimated_shipping': estimated_shipping,
        'grand_total': grand_total,
        'insufficient_stock': insufficient_stock,
        'total_quantity': total_quantity,
    }

    return render(request, 'orders/cart.html', context)


@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.delete()
    messages.info(request, "Item removed from cart.")
    return redirect('view_cart')


@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    if not cart_items:
        messages.error(request, "Your cart is empty.")
        return redirect('view_cart')

    # --- Calculate estimated costs for initial display ---
    subtotal = Decimal('0.00')
    estimated_shipping = Decimal('0.00')
    shipping_rates = ShippingRate.objects.all()

    for item in cart_items:
        subtotal += item.get_total_price()
        item_shipping_cost = Decimal('0.00')
        for rate in shipping_rates:
            if item.product.weight_in_grams <= rate.weight_slab_grams:
                item_shipping_cost = rate.regional_rate  # Use regional rate for estimation
                break
        estimated_shipping += item_shipping_cost * item.quantity

    grand_total = subtotal + estimated_shipping
    # --- End of calculation ---

    saved_addresses = ShippingAddress.objects.filter(user=request.user)
    shipping_form = ShippingForm()  # For entering a new address

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'estimated_shipping': estimated_shipping,
        'grand_total': grand_total,
        'saved_addresses': saved_addresses,
        'shipping_form': shipping_form,
    }

    return render(request, 'orders/checkout.html', context)


@login_required
def place_order(request):
    cart_items = CartItem.objects.select_related('product', 'product__artisan').filter(user=request.user)
    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('view_cart')

    if request.method == "POST":
        # Step 1: Get the customer's shipping address
        use_saved = request.POST.get('use_saved')
        shipping_form = ShippingForm(request.POST)
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
            messages.error(request, "Invalid shipping details.")
            return redirect('checkout')

        # Step 2: Calculate FINAL, ACCURATE costs with COMBINED SHIPPING
        subtotal = Decimal('0.00')
        final_shipping_cost = Decimal('0.00')
        shipping_rates = ShippingRate.objects.all()
        customer_state = shipping_data.get('state', '').strip().lower()

        artisan_packages = defaultdict(lambda: {'total_weight': 0, 'artisan_state': ''})
        for item in cart_items:
            subtotal += item.get_total_price()
            artisan_id = item.product.artisan.id
            artisan_state = item.product.artisan.state.strip().lower()
            artisan_packages[artisan_id]['artisan_state'] = artisan_state
            artisan_packages[artisan_id]['total_weight'] += item.product.weight_in_grams * item.quantity

        for artisan_id, package_data in artisan_packages.items():
            total_weight = package_data['total_weight']
            artisan_state = package_data['artisan_state']
            package_shipping_cost = Decimal('0.00')

            is_regional = (customer_state == artisan_state)

            for rate in shipping_rates:
                if total_weight <= rate.weight_slab_grams:
                    package_shipping_cost = rate.regional_rate if is_regional else rate.national_rate
                    break

            final_shipping_cost += package_shipping_cost

        grand_total = subtotal + final_shipping_cost

        if grand_total <= 0:
            messages.error(request, "Total amount must be greater than zero.")
            return redirect('view_cart')

        # Step 3: Create Razorpay order
        try:
            razorpay_order = razorpay_client.order.create({
                "amount": int(grand_total * 100),
                "currency": "INR",
                "receipt": f"receipt_{request.user.id}_{cart_items.count()}",
                "payment_capture": 1
            })
        except Exception as e:
            logger.error(f"Razorpay order creation failed: {str(e)}")
            messages.error(request, "Payment initiation failed. Please try again.")
            return redirect('checkout')

        # Step 4: Store data in session
        request.session['shipping_data'] = shipping_data
        request.session['final_shipping_cost'] = str(final_shipping_cost)
        request.session['razorpay_order_id'] = razorpay_order['id']

        return render(request, 'orders/payment.html', {
            "razorpay_order_id": razorpay_order['id'],
            "razorpay_key": settings.RAZORPAY_KEY_ID,
            "amount": int(grand_total * 100),
            "total_amount": grand_total
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
        # ✅ Add `request` as the first argument
        messages.success(request, f"{product.name} moved to your wishlist.")
    else:
        # ✅ Add `request` as the first argument
        messages.info(request, f"{product.name} is already in your wishlist.")

    return redirect('view_cart')


@login_required
def move_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if product.stock <= 0:
        messages.error(request, f"{product.name} is out of stock.")
        return redirect('view_wishlist')

    WishlistItem.objects.filter(user=request.user, product=product).delete()

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={'quantity': 1}
    )

    if not created:
        if cart_item.quantity < product.stock:
            cart_item.quantity += 1
            cart_item.save()
        else:
            messages.warning(request, f"Cannot add more of {product.name}; only {product.stock} in stock.")
            # WishlistItem.objects.get_or_create(user=request.user, product=product)
            return redirect('view_wishlist')

    # ✅ Add `request` as the first argument here
    messages.success(request, f"'{product.name}' was moved to your cart.")

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
        elif new_quantity > item.product.stock:
            return JsonResponse({'error': f"Only {item.product.stock} in stock."}, status=400)
        else:
            item.quantity = new_quantity
            item.save()

        # --- CORRECT, COMBINED SHIPPING LOGIC ---
        cart_items = CartItem.objects.filter(user=request.user)
        subtotal = Decimal('0.00')
        estimated_shipping = Decimal('0.00')

        # Step 1: Group items and weights by artisan
        artisan_packages = defaultdict(lambda: {'total_weight': 0})
        for cart_item in cart_items:
            subtotal += cart_item.get_total_price()
            artisan_id = cart_item.product.artisan.id
            artisan_packages[artisan_id]['total_weight'] += cart_item.product.weight_in_grams * cart_item.quantity

        # Step 2: Calculate shipping for each artisan's package
        shipping_rates = ShippingRate.objects.all()
        for artisan_id, package_data in artisan_packages.items():
            total_weight = package_data['total_weight']
            package_shipping_cost = Decimal('0.00')
            for rate in shipping_rates:
                if total_weight <= rate.weight_slab_grams:
                    package_shipping_cost = rate.regional_rate
                    break
            estimated_shipping += package_shipping_cost
        # --- END OF CORRECT LOGIC ---

        grand_total = subtotal + estimated_shipping
        total_quantity = sum(i.quantity for i in cart_items)

        if new_quantity < 1:
            return JsonResponse({
                'removed': True,
                'item_id': item_id,
                'subtotal': float(subtotal),
                'estimated_shipping': float(estimated_shipping),
                'grand_total': float(grand_total),
                'total_quantity': total_quantity
            })

        return JsonResponse({
            'success': True,
            'quantity': item.quantity,
            'item_total': float(item.get_total_price()),
            'subtotal': float(subtotal),
            'estimated_shipping': float(estimated_shipping),
            'grand_total': float(grand_total),
            'total_quantity': total_quantity
        })

    # ✅ FIX: Corrected the typo from 4G05 to 405
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
            return JsonResponse({"error": "Missing payment information"}, status=400)

        # Step 1: Verify the payment signature
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature,
        })

        # Step 2: Process the order in a secure transaction
        with transaction.atomic():
            cart_items = CartItem.objects.select_related('product').filter(user=request.user).select_for_update()
            if not cart_items.exists():
                return JsonResponse({"error": "Your cart is empty."}, status=400)

            # ✅ Recalculate subtotal and get final shipping cost from session
            subtotal = sum(item.get_total_price() for item in cart_items)
            final_shipping_cost = Decimal(request.session.get('final_shipping_cost', '0.00'))
            grand_total = subtotal + final_shipping_cost

            shipping_data = request.session.get('shipping_data', {})

            # ✅ Create the final order with the full cost breakdown
            order = Order.objects.create(
                buyer=request.user,
                subtotal=subtotal,
                shipping_cost=final_shipping_cost,
                total_amount=grand_total,  # This is the grand total
                payment_status='successful',
                status='confirmed',
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=payment_id,
                razorpay_signature=signature,
                **shipping_data
            )

            # Create order items and update stock
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )
                item.product.stock = F('stock') - item.quantity
                item.product.save(update_fields=['stock'])

            # Step 3: Clean up session
            cart_items.delete()
            request.session.pop('shipping_data', None)
            request.session.pop('final_shipping_cost', None)
            request.session.pop('razorpay_order_id', None)

        return JsonResponse({"status": "success", "order_id": order.id})

    except razorpay.errors.SignatureVerificationError:
        logger.warning("Payment verification failed: Signature mismatch.")
        return JsonResponse({"error": "Signature verification failed"}, status=400)
    except Exception as e:
        logger.error(f"An unexpected error occurred in payment verification: {str(e)}")
        return JsonResponse({"error": "An internal server error occurred."}, status=500)

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


@login_required
def calculate_shipping_view(request):
    if request.method == 'POST':
        customer_state = request.POST.get('state', '').strip().lower()
        cart_items = CartItem.objects.filter(user=request.user)

        if not customer_state or not cart_items.exists():
            return JsonResponse({'error': 'State or cart items missing.'}, status=400)

        # --- Use our combined shipping logic ---
        subtotal = Decimal('0.00')
        final_shipping_cost = Decimal('0.00')
        shipping_rates = ShippingRate.objects.all()

        artisan_packages = defaultdict(lambda: {'total_weight': 0, 'artisan_state': ''})
        for item in cart_items:
            subtotal += item.get_total_price()
            artisan_id = item.product.artisan.id
            artisan_state = item.product.artisan.state.strip().lower()
            artisan_packages[artisan_id]['artisan_state'] = artisan_state
            artisan_packages[artisan_id]['total_weight'] += item.product.weight_in_grams * item.quantity

        for artisan_id, package_data in artisan_packages.items():
            total_weight = package_data['total_weight']
            artisan_state = package_data['artisan_state']
            package_shipping_cost = Decimal('0.00')
            is_regional = (customer_state == artisan_state)

            for rate in shipping_rates:
                if total_weight <= rate.weight_slab_grams:
                    package_shipping_cost = rate.regional_rate if is_regional else rate.national_rate
                    break
            final_shipping_cost += package_shipping_cost

        grand_total = subtotal + final_shipping_cost

        return JsonResponse({
            'success': True,
            'shipping_cost': float(final_shipping_cost),
            'grand_total': float(grand_total)
        })

    return JsonResponse({'error': 'Invalid request method.'}, status=405)