from django.core.mail import send_mail
from django.conf import settings


def clean_text(text):
    # Replace non-breaking spaces and ensure it's all UTF-8 safe
    return text.replace('\xa0', ' ').strip()


def send_approval_email(user):
    subject = clean_text("✅ Your Artisan Account Has Been Approved")
    message = clean_text(f"""
Hi {user.username},

Congratulations! Your artisan account has been approved by the Aarta admin team.

You can now log in and start listing your creations.

Regards,  
Aarta Team
""")
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


def send_rejection_email(user):
    subject = clean_text("❌ Your Artisan Account Request Was Rejected")
    message = clean_text(f"""
Hi {user.username},

We're sorry to inform you that your artisan account request has been rejected after review.

If you believe this was a mistake or need help, feel free to reach out to support.

Regards,  
Aarta Team
""")
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
