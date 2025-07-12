
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from orders.models import OrderItem
from .forms import ProductForm
from .models import Product, ProductImage
from users.models import ArtisanProfile


def home(request):
    featured_products = Product.objects.filter(is_featured=True, is_approved=True)[:6]
    return render(request, 'index.html', {'featured_products': featured_products})


def product_gallery(request):
    products = Product.objects.filter(is_approved=True).order_by('-created_at')
    return render(request, 'products/product_gallery.html', {'products': products})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if not product.is_approved and not request.user.is_staff:
        return redirect('product_gallery')
    return render(request, 'products/product_detail.html', {'product': product})


@login_required
def add_product(request):
    try:
        artisan_profile = request.user.artisanprofile
    except ArtisanProfile.DoesNotExist:
        return redirect('dashboard')

    if request.method == 'POST':
        form = ProductForm(request.POST)
        images = request.FILES.getlist('images')

        if form.is_valid():
            product = form.save(commit=False)
            product.artisan = artisan_profile
            product.save()

            for image in images:
                ProductImage.objects.create(product=product, image_path=image)

            return redirect('my_products')
    else:
        form = ProductForm()

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
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('my_products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'products/edit_product.html', {'form': form})


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
            .filter(product__artisan=artisan)
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
