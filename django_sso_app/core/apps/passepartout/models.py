# import uuid

from django.db import models, IntegrityError
from django.utils.translation import ugettext_lazy as _

from ...utils import get_random_token
from ...models import CreatedAtModel, UpdatableModel, DeactivableModel
from ..devices.models import Device
from ... import app_settings

from .settings import CODE_LENGTH


class PassepartoutManager(models.Manager):

    def create_passepartout(self, device, jwt):
        passepartout = self.create(
            device=device,
            jwt=jwt,
            token=Passepartout.generate_token()
        )
        try:
            passepartout.save()
        except IntegrityError:
            # Try again with other code
            passepartout = Passepartout.objects.create_passepartout(device, jwt)

        return passepartout


class Passepartout(CreatedAtModel, UpdatableModel, DeactivableModel):
    class Meta:
        app_label = 'django_sso_app'
        verbose_name = _('Passepartout')
        unique_together = ('token', 'is_active')

    objects = PassepartoutManager()

    # deleted = models.BooleanField(_('deleted'), default=False)
    token = models.CharField(_('token'), unique=True, db_index=True, max_length=36)
    jwt = models.TextField(_('jwt'), null=True, blank=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, verbose_name=_('device'))
    bumps = models.PositiveIntegerField(_('bumps'), default=len(app_settings.BACKEND_DOMAINS) - 1)

    @classmethod
    def generate_token(cls):
        return get_random_token(CODE_LENGTH)

    def __str__(self):
        return '{0}:{1}'.format(self.id, self.device.fingerprint)

    @property
    def user(self):
        return self.device.user
