from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect

from products.models import Product
from users.forms import RegisterForm, ArtisanProfileForm
from users.models import ArtisanProfile


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            is_artisan = request.POST.get('is_artisan') == 'on'
            user.is_artisan = is_artisan
            user.save()

            login(request, user)

            # Redirect artisans to pending approval page
            if user.is_artisan:
                messages.info(request, "Your artisan registration is submitted. Please wait for admin approval.")
                return redirect('pending_approval')
            else:
                return redirect('home')
    else:
        form = RegisterForm()

    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)

            if user.is_artisan:
                if not user.is_approved_artisan:
                    messages.warning(request, "Your artisan profile is pending admin approval.")
                    return redirect('pending_approval')
                return redirect('artisan_dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'users/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def artisan_dashboard(request):
    if not request.user.is_artisan or not request.user.is_approved_artisan:
        messages.error(request, "Access denied. You must be an approved artisan.")
        return redirect('home')

    products = Product.objects.filter(artisan=request.user.artisanprofile)
    return render(request, 'users/dashboard.html', {
        'user': request.user,
        'products': products
    })


@login_required
def buyer_dashboard(request):
    return render(request, 'users/buyer_dashboard.html')


@login_required
def edit_artisan_profile(request):
    if not request.user.is_artisan:
        return redirect('home')

    profile, created = ArtisanProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ArtisanProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('artisan_dashboard')
    else:
        form = ArtisanProfileForm(instance=profile)

    return render(request, 'users/edit_artisan_profile.html', {'form': form})


# ✅ Pending approval view
@login_required
def pending_approval_view(request):
    if not request.user.is_artisan or request.user.is_approved_artisan:
        return redirect('home')
    return render(request, 'users/pending_approval.html')
