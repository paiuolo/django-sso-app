import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse

from ..profiles.models import Profile
from ...models import CreatedAtModel, DeactivableModel

logger = logging.getLogger('django_sso_app')


class Device(CreatedAtModel, DeactivableModel):
    # deleting deletes jwt by delete_device_jwt signal!
    class Meta:
        app_label = 'django_sso_app'
        verbose_name = _('Device')

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="devices",
        verbose_name=_('profile')
    )

    fingerprint = models.CharField(_('fingerprint'), max_length=32)
    user_agent = models.CharField(_('user agent'), max_length=32, null=True, blank=True)

    apigw_jwt_id = models.CharField(_('apigw_jwt_id'), max_length=36, null=True, blank=True)
    apigw_jwt_key = models.CharField(_('apigw_jwt_key'), max_length=32, null=True, blank=True)
    apigw_jwt_secret = models.CharField(_('apigw_jwt_secret'), max_length=32, null=True, blank=True)

    def __str__(self):
        return '{}:{}:{}'.format(self.id, self.fingerprint, self.apigw_jwt_id)

    def get_relative_rest_url(self):
        return reverse("django_sso_app_device:rest-detail", args=[self.pk])

    def get_jwt_payload(self):
        return {
            'id': self.id,
            'fp': self.fingerprint,
            'sso_id': str(self.profile.sso_id),
            'sso_rev': self.profile.sso_rev,
            'iss': self.apigw_jwt_key,
            # 'iat': datetime.utcnow()
        }

    @property
    def user(self):
        return self.profile.user
