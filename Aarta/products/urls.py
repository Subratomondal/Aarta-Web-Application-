from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Public-facing URLs
    path('', views.home, name='home'),
    path('gallery/', views.product_gallery, name='product_gallery'),



    # CRUD URLs for Products, grouped under 'product/'
    path('product/add/', views.add_product, name='add_product'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('product/<int:pk>/edit/', views.edit_product, name='edit_product'),
    path('product/<int:pk>/delete/', views.delete_product, name='delete_product'),
    path('product/image/<int:image_id>/delete/', views.delete_product_image, name='delete_product_image'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
