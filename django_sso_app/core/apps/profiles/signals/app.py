import logging

from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model

from ..utils import get_or_create_user_profile

logger = logging.getLogger('django_sso_app')

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    App still creates profile for "staff" users
    """
    if kwargs['raw']:
        # setting property flag
        setattr(instance, '__dssoa__loaddata', True)
        # https://github.com/django/django/commit/18a2fb19074ce6789639b62710c279a711dabf97
        return

    user = instance

    if created:
        logger.debug('user created, creating profile')

        profile = get_or_create_user_profile(user, commit=True)

        logger.debug('new profile created "{}"'.format(profile))

        # refreshing user instance
        user.sso_app_profile = profile
