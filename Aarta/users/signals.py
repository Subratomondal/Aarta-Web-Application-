from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import ArtisanProfile, BuyerProfile

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender,instance,created, **kwargs):
    if created:
        if instance.is_artisan:
            ArtisanProfile.objects.create(user=instance)
        else:
            BuyerProfile.objects.create(user=instance)