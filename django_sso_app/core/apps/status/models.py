import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _

from ...models import UuidPKModel, CreatedAtModel, UpdatableModel
from ... import app_settings

logger = logging.getLogger('django_sso_app')


class Status(UuidPKModel, CreatedAtModel, UpdatableModel):
    """
    Should use django migrations to keep track of status switch
    """
    class Meta:
        app_label = 'django_sso_app'
        verbose_name = _('Status')

    shape = models.CharField(max_length=255, default=app_settings.SHAPE)

    def __str__(self):
        return self.shape
