"""
Signal handlers for Accounts app.
Creates UserAccount automatically when a User is created.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import UserAccount


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_account(sender, instance, created, **kwargs):
    """Create a UserAccount when a new User is created."""
    if created:
        UserAccount.objects.get_or_create(user=instance)
