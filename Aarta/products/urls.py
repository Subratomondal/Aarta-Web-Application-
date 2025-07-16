from django.urls import path

from products import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns =[
    path('', views.home, name='home'),
    path('gallery/', views.product_gallery, name='product_gallery'),
    path('add/',views.add_product,name='add_product'),
    path('my-products/',views.my_products,name='my_products'),
    path('edit/<int:pk>',views.edit_product,name='edit_product'),
    path('delete/<int:pk>',views.delete_product,name='delete_product'),
    path('dashboard/',views.artisan_dashboard,name='artisan_dashboard'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('<int:image_id>/delete-image/', views.delete_product_image, name='delete_product_image'),


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

