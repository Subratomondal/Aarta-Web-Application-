# In core/views.py

from django.views.generic import TemplateView


# These views simply render a static HTML template.
# We will create these templates in the next step.

class TermsOfServiceView(TemplateView):
    template_name = "core/terms_of_service.html"


class PrivacyPolicyView(TemplateView):
    template_name = "core/privacy_policy.html"


class ReturnPolicyView(TemplateView):
    template_name = "core/return_policy.html"


class SellerGuidelinesView(TemplateView):
    template_name = "core/seller_guidelines.html"


from django.shortcuts import render

# Create your views here.
