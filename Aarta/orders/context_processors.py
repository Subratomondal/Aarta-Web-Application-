from .models import CartItem, WishlistItem


def cart_item_count(request):
    if request.user.is_authenticated and not request.user.is_artisan:
        count = CartItem.objects.filter(user=request.user).count()
    else:
        count = 0
    return {'cart_item_count': count}

def wishlist_count(request):
    if request.user.is_authenticated:
        count = WishlistItem.objects.filter(user=request.user).count()
    else:
        count = 0
    return {'wishlist_count': count}