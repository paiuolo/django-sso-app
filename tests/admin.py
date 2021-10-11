from django.contrib import admin
from django.contrib.auth import get_user_model

from django_sso_app.core.apps.users.admin import UserAdmin

User = get_user_model()


admin.site.register(User, UserAdmin)
