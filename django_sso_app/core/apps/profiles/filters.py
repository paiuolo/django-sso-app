from django.contrib.auth import get_user_model

from django_filters import rest_framework as filters

from .models import Profile


class ProfileFilter(filters.FilterSet):
    class Meta:
        model = Profile
        fields = {
            'user__username': ['exact'],
            'sso_id': ['exact'],
            'groups__name': ['exact'],
        }
