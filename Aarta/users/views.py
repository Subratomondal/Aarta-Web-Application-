from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from products.models import Product
from users.forms import RegisterForm


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            # Checkbox handling
            is_artisan = request.POST.get('is_artisan') == 'on'
            user.is_artisan = is_artisan

            user.save()
            login(request, user)  # Optional: log them in immediately

            return redirect('artisan_dashboard' if user.is_artisan else 'home')
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
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'users/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def artisan_dashboard(request):
    if not request.user.is_artisan:
        return redirect('home')  # or show access denied message

    products = Product.objects.filter(artisan=request.user.artisanprofile)

    return render(request, 'users/dashboard.html',
                  {
                      'user': request.user,
                      'products': products
                  })


from django.shortcuts import render, redirect

@login_required
def buyer_dashboard(request):
    return render(request, 'users/buyer_dashboard.html')

