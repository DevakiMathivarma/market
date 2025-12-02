from django.dispatch import receiver
from django.db.models.signals import post_save
from core.models import UserProductInteraction

# Wishlist
@receiver(post_save, sender=UserProductInteraction)
def interaction_logger(sender, instance, **kwargs):
    pass  # currently unused, reserved for analytics
