from django.contrib import admin

from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .models import Grouping


class GroupingAdmin(TreeAdmin):
    form = movenodeform_factory(Grouping)
    list_display = ('name', 'type', 'group')
    search_fields = ('name', 'type', 'group__name')


admin.site.register(Grouping, GroupingAdmin)
