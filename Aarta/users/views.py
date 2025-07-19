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

            # ✅ Get the value from the form's validated data
            user.is_artisan = form.cleaned_data.get('is_artisan', False)
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
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            # This is the correct logic: it redirects every user to the single
            # 'dashboard' dispatch view, which then handles routing them to the
            # correct page (artisan, buyer, or pending).
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'users/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')




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

@login_required
def dashboard_dispatch_view(request):
    # ✅ Add the approval check here
    if request.user.is_artisan and request.user.is_approved_artisan:
        return redirect('artisan_dashboard')
    elif request.user.is_artisan:
        # If they are an artisan but not approved, send them to the pending page
        return redirect('pending_approval')
    else:
        # Otherwise, they are a buyer
        return redirect('buyer_dashboard')