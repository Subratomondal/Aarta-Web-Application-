import logging
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings

# Set up logger for emails
logger = logging.getLogger(__name__)

def clean_text(text):
    # Replace non-breaking spaces and strip surrounding whitespace
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
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        logger.info(f"Approval email sent to {user.email}")
    except BadHeaderError:
        logger.error(f"BadHeaderError while sending approval email to {user.email}")
    except Exception as e:
        logger.error(f"Error sending approval email to {user.email}: {str(e)}")

def send_rejection_email(user):
    subject = clean_text("❌ Your Artisan Account Request Was Rejected")
    message = clean_text(f"""
Hi {user.username},

We're sorry to inform you that your artisan account request has been rejected after review.

If you believe this was a mistake or need help, feel free to reach out to support.

Regards,  
Aarta Team
""")
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        logger.info(f"Rejection email sent to {user.email}")
    except BadHeaderError:
        logger.error(f"BadHeaderError while sending rejection email to {user.email}")
    except Exception as e:
        logger.error(f"Error sending rejection email to {user.email}: {str(e)}")

