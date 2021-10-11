from django.contrib import admin

from .models import Profile


class ProfileAdmin(admin.ModelAdmin):
    search_fields = ('id', 'sso_id', 'user__username', 'user__email')
    list_display = ('user', 'sso_id', 'sso_rev', 'created_at', 'created_by_event')
    filter_horizontal = ('groups', )


admin.site.register(Profile, ProfileAdmin)
