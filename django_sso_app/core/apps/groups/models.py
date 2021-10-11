import logging

from django.db import models
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse

from treebeard.mp_tree import MP_Node, MP_NodeManager

from ...models import CreatedAtModel

logger = logging.getLogger('django_sso_app')


"""
class Group(DjangoGroup):
    class Meta:
        proxy = True
        app_label = 'django_sso_app'
        verbose_name = _('Group')

    def get_relative_rest_url(self):
        return reverse("django_sso_app_group:rest-detail", args=[self.pk])
"""


class GroupingManager(MP_NodeManager):
    pass


class Grouping(MP_Node, CreatedAtModel):
    class Meta:
        app_label = 'django_sso_app'
        verbose_name = _('Grouping')

    name = models.CharField(_("name"), max_length=150)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    type = models.CharField(_("type"), max_length=255, null=True, blank=True)
    description = models.TextField(_('description'), null=True, blank=True)

    objects = GroupingManager()
    node_order_by = ('name', )  # treebeard mp_node ordering

    def get_relative_rest_url(self):
        return reverse("django_sso_app_group:rest-grouping-detail", args=[self.pk])
