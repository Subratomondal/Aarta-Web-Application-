from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from users.models import ArtisanProfile, BuyerProfile

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.is_artisan:
            ArtisanProfile.objects.create(user=instance)
        else:
            BuyerProfile.objects.create(user=instance)

@receiver(post_delete, sender=ArtisanProfile)
def remove_artisan_flag(sender, instance, **kwargs):
    user = instance.user
    user.is_artisan = False
    user.save()
