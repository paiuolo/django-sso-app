"""from django.contrib import admin

from .models import Status


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('shape', 'created_at')


admin.site.register(Status, StatusAdmin)
"""