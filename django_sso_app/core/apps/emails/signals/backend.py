import logging

from django.dispatch import receiver
from django.db.models.signals import post_save

from allauth.account.models import EmailAddress

logger = logging.getLogger('django_sso_app')


@receiver(post_save, sender=EmailAddress)
def email_addresses_updated(sender, instance, created, **kwargs):
    """
    Manage email model updates, only one primary/verified email per user
    """

    if kwargs['raw']:
        # https://github.com/django/django/commit/18a2fb19074ce6789639b62710c279a711dabf97
        return

    if instance.primary and instance.verified:
        user = instance.user

        # deleting all other user email addresses
        for email_address in user.emailaddress_set.exclude(pk=instance.pk).all():
            logger.info('Email "{}" primary and verified, deleting "{}"'.format(instance, email_address))

            email_address.delete()

    if not instance.verified:
        user = instance.user

        # deleting all other user email addresses
        for email_address in user.emailaddress_set.exclude(pk=instance.pk).filter(verified=False):
            logger.info('Email "{}" not verified, deleting "{}"'.format(instance, email_address))

            email_address.delete()
