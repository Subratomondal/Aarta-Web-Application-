"""
URL configuration for Aarta project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
                  path('admin/', admin.site.urls),

                  # User-related URLs (login, register, dashboard) are now under /accounts/
                  path('accounts/', include('users.urls')),

                  # Order-related URLs (cart, checkout) are under /orders/
                  path('orders/', include('orders.urls')),

                  # Product/public URLs (homepage, gallery) are at the root
                  path('', include('products.urls')),
                  path('', include('core.urls')),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)