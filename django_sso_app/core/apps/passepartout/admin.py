from django.contrib import admin

from .models import Passepartout


class PassepartoutAdmin(admin.ModelAdmin):
    search_fields = ('id', 'device__profile__sso_id',
                     'device__profile__user__username',
                     'device__profile__user__email')
    list_display = ('user', 'is_active', 'created_at')


admin.site.register(Passepartout, PassepartoutAdmin)
