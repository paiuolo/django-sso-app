from django.contrib import admin

from .models import Device


class DeviceAdmin(admin.ModelAdmin):
    search_fields = ('id', 'fingerprint', 'profile__sso_id', 'profile__user__username', 'profile__user__email')
    list_display = ('user', 'fingerprint', 'created_at')


admin.site.register(Device, DeviceAdmin)
