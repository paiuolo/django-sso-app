import uuid
import json

from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import FieldError


class UuidPKModel():
    class Meta:
        abstract = True

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class DeactivableModel(models.Model):
    class Meta:
        abstract = True

    is_active = models.BooleanField(_("is active"), default=True)


class CreatedAtModel(models.Model):
    class Meta:
        abstract = True

    created_at = models.DateTimeField(_("created at"),
                                      editable=False,
                                      auto_now_add=True)


class UpdatableModel(models.Model):
    class Meta:
        abstract = True

    updated_at = models.DateTimeField(_("updated at"),
                                      editable=False,
                                      null=True,
                                      blank=True)

    def save(self, *args, **kwargs):
        if not self._state.adding:
            self.updated_at = timezone.now()
        return super(UpdatableModel, self).save(*args, **kwargs)


class PublicableModel(models.Model):
    class Meta:
        abstract = True

    is_public = models.BooleanField(_('is public'), default=False)


class TimespanModel(models.Model):
    class Meta:
        abstract = True

    started_at = models.DateTimeField(_("started at"), null=True, blank=True)

    ended_at = models.DateTimeField(_("ended at"), null=True, blank=True)


class MetaFieldModel(models.Model):
    class Meta:
        abstract = True

    meta = models.TextField(verbose_name=_('Meta'),
                            null=True,
                            blank=True)

    def save(self, *args, **kwargs):
        if self.meta is not None and self.meta.strip() == '':
            self.meta = None
        else:
            if self.meta is not None:
                try:
                    json.loads(self.meta)
                except ValueError:
                    raise FieldError('Invalid JSON on meta field')

        return super(MetaFieldModel, self).save(*args, **kwargs)

