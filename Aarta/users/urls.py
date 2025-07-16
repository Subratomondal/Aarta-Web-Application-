from django.urls import path

from users import views

urlpatterns = [
    path('register/',views.register_view,name='register'),
    path('pending-approval/', views.pending_approval_view, name='pending_approval'),
    path('login/',views.login_view,name='login'),
    path('logout/',views.logout_view,name='logout'),
    path('dashboard/',views.artisan_dashboard,name='artisan_dashboard'),
    path('buyer-dashboard/', views.buyer_dashboard, name='buyer_dashboard'),
    path('artisan/edit/', views.edit_artisan_profile, name='edit_artisan_profile'),

]