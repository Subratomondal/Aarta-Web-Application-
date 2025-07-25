from django.urls import path
from . import views

urlpatterns = [
    # Cart Management
    path('cart/', views.view_cart, name='view_cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_quantity, name='update_cart_quantity'),

    # Checkout and Order Process
    path('checkout/', views.checkout, name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path('payment/<int:order_id>/', views.payment_page, name='payment_page'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),

    # User Account and Order History
    path('my-orders/', views.my_orders, name='my_orders'),
    path('my-addresses/', views.saved_addresses, name='my_addresses'),
    # ✅ ADD THIS NEW URL for deleting an address
    path('my-addresses/delete/<int:address_id>/', views.delete_address, name='delete_address'),
    path('order/<int:order_id>/track/', views.track_order, name='track_order'),
    path('order/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),

    # Wishlist Management
    path('wishlist/', views.view_wishlist, name='view_wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/move-to-cart/<int:product_id>/', views.move_to_cart, name='move_to_cart'),
    path('cart/move-to-wishlist/<int:product_id>/', views.move_to_wishlist, name='move_to_wishlist'),

    # API Endpoints
    path('api/cancel-pending-payment/<int:order_id>/', views.api_cancel_pending_payment, name='api_cancel_pending_payment'),
    path('api/calculate-shipping/', views.calculate_shipping_view, name='calculate_shipping'),
]
