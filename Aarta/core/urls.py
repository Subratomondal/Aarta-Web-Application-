# In core/urls.py

from django.urls import path
from .views import (
    TermsOfServiceView,
    PrivacyPolicyView,
    ReturnPolicyView,
    SellerGuidelinesView,
)

urlpatterns = [
    path('terms-of-service/', TermsOfServiceView.as_view(), name='terms_of_service'),
    path('privacy-policy/', PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('return-policy/', ReturnPolicyView.as_view(), name='return_policy'),
    path('seller-guidelines/', SellerGuidelinesView.as_view(), name='seller_guidelines'),
]