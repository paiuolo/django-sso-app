import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver

from django_sso_app.core.apps.status.models import Status

logger = logging.getLogger('django_sso_app')


@receiver(pre_save, sender=Status)
def state_pre_save(sender, instance, **kwargs):
    """
    Status model has been updated
    """

    if instance._state.adding:
        logger.info('Status updated, syncing..')
