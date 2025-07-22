from django.urls import path

from products.views import artisan_dashboard
from . import views

urlpatterns = [
    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('pending-approval/', views.pending_approval_view, name='pending_approval'),

    # Dashboards (with a single entry point)
    path('dashboard/', views.dashboard_dispatch_view, name='dashboard'),  # Generic entry point
    path('dashboard/artisan/', artisan_dashboard, name='artisan_dashboard'),  # Specific artisan URL
    path('dashboard/buyer/', views.buyer_dashboard, name='buyer_dashboard'),  # Specific buyer URL

    # Profile Management
    path('profile/artisan/edit/', views.edit_artisan_profile, name='edit_artisan_profile'),
    path('profile/payout-settings/', views.payout_settings_view, name='payout_settings'),
]