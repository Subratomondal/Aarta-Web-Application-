from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required


from orders.models import OrderItem, WishlistItem, Order
from .forms import ProductForm
from .models import Product, ProductImage, Category
from users.models import ArtisanProfile



def home(request):
    featured_products = Product.objects.filter(is_featured=True, is_approved=True)[:6]
    featured_categories = Category.objects.filter(is_featured=True)[:4]  # admin controls which are shown
    return render(request, 'index.html', {
        'featured_products': featured_products,
        'categories': featured_categories
    })



def product_gallery(request):
    products = Product.objects.filter(is_approved=True)
    categories = Category.objects.all()

    # Category Filter
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)

    # Sorting
    sort_option = request.GET.get('sort')
    if sort_option == 'price_asc':
        products = products.order_by('price')
    elif sort_option == 'price_desc':
        products = products.order_by('-price')
    elif sort_option == 'newest':
        products = products.order_by('-created_at')

    context = {
        'products': products,
        'categories': categories,
        'selected_category': category_id,
        'sort_option': sort_option,
    }

    return render(request, 'products/product_gallery.html', context)


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if not product.is_approved and not request.user.is_staff:
        return redirect('product_gallery')

    is_wishlisted = False
    if request.user.is_authenticated:
        is_wishlisted = WishlistItem.objects.filter(user=request.user, product=product).exists()

    return render(request, 'products/product_detail.html', {
        'product': product,
        'is_wishlisted': is_wishlisted  # ✅ Pass to template
    })


@login_required
def add_product(request):
    try:
        artisan_profile = request.user.artisanprofile
    except ArtisanProfile.DoesNotExist:
        return redirect('dashboard')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, request=request)
        images = request.FILES.getlist('images')

        if form.is_valid():
            product = form.save(commit=False)
            product.artisan = artisan_profile
            product.save()

            for image in images:
                ProductImage.objects.create(product=product, image_path=image)

            return redirect('my_products')
    else:
        form = ProductForm(request=request)

    return render(request, 'products/add_product.html', {'form': form})


@login_required
def my_products(request):
    try:
        artisan_profile = request.user.artisanprofile
        products = Product.objects.filter(artisan=artisan_profile)
    except ArtisanProfile.DoesNotExist:
        products = []
    return render(request, 'products/my_products.html', {'products': products})


@login_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk, artisan=request.user.artisanprofile)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product, request=request)
        images = request.FILES.getlist('images')

        if form.is_valid():
            form.save()
            for image in images:
                ProductImage.objects.create(product=product, image_path=image)
            return redirect('my_products')
    else:
        form = ProductForm(instance=product, request=request)

    images = product.images.all()
    remaining_uploads = 4 - images.count()

    return render(request, 'products/edit_product.html', {
        'form': form,
        'product': product,
        'images': images,
        'remaining_uploads': remaining_uploads
    })



@login_required
def delete_product_image(request, image_id):
    image = get_object_or_404(ProductImage, id=image_id, product__artisan=request.user.artisanprofile)
    product_id = image.product.id
    image.delete()
    return redirect('edit_product', pk=product_id)


@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk, artisan=request.user.artisanprofile)
    if request.method == 'POST':
        product.delete()
        return redirect('my_products')
    return render(request, 'products/confirm_delete.html', {'product': product})


@login_required
def artisan_dashboard(request):
    try:
        artisan = request.user.artisanprofile
        products = Product.objects.filter(artisan=artisan)
        total_products = products.count()
        total_orders = OrderItem.objects.filter(product__artisan=artisan).values('order').distinct().count()
        recent_product = products.order_by('-created_at').first()

        top_selling = (
            OrderItem.objects
            .filter(product__artisan=artisan)
            .values('product__name')
            .annotate(total_sold=Sum('quantity'))
            .order_by('-total_sold')
            .first()
        )

        recent_orders = (
            OrderItem.objects
            .filter(
                product__artisan=artisan,
                order__status__in=['pending', 'processing', 'confirmed', 'shipped']  # only active statuses
            )
            .select_related('order', 'product')
            .order_by('-order__created_at')[:5]
        )

        context = {
            'products': products,
            'total_products': total_products,

            'total_orders': total_orders,
            'recent_product': recent_product,
            'top_selling': top_selling,
            'recent_orders': recent_orders,
        }

        return render(request, 'products/artisan_dashboard.html', context)

    except ArtisanProfile.DoesNotExist:
        return redirect('home')

@login_required
def update_order_status(request, order_id):
    if request.method == 'POST':
        new_status = request.POST.get('status')

        # Get the order only if it contains items by this artisan
        order = get_object_or_404(Order, id=order_id, items__product__artisan=request.user.artisanprofile)

        valid_transitions = {
            'pending': 'confirmed',
            'confirmed': 'shipped',
        }

        if valid_transitions.get(order.status) == new_status:
            order.status = new_status
            order.save()
            messages.success(request, f"Order marked as {new_status.capitalize()}.")
        else:
            messages.warning(request, "Invalid status transition.")

    return redirect('artisan_dashboard')