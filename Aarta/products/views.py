from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProductForm
from .models import Product
from users.models import ArtisanProfile
from django.contrib.auth.decorators import login_required


@login_required
def add_product(request):
    try:
        artisan_profile = request.user.artisanprofile
    except ArtisanProfile.DoesNotExist:
        return redirect('dashboard')  # or show an error

    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.artisan = artisan_profile
            product.save()
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


from django.shortcuts import render


@login_required
def artisan_dashboard(request):
    # Ensure the user is an artisan
    try:
        artisan = request.user.artisanprofile  # Get ArtisanProfile linked to User
        products = Product.objects.filter(artisan=artisan)
    except ArtisanProfile.DoesNotExist:
        return redirect('home')  # or show an error page

    return render(request, 'products/artisan_dashboard.html', {
        'products': products
    })
