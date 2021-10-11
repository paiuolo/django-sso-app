from django.contrib import admin

from .models import RequestForCredentialsEventListener


class RequestForCredentialsEventListenerAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'created_at', 'is_active')
    search_fields = ('event_type',)


admin.site.register(RequestForCredentialsEventListener, RequestForCredentialsEventListenerAdmin)
