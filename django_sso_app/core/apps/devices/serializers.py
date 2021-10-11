import logging

from rest_framework import serializers

from ...serializers import AbsoluteUrlSerializer
from .models import Device

logger = logging.getLogger('django_sso_app')


class DeviceSerializer(AbsoluteUrlSerializer):
    profile = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Device
        fields = ('url', 'id', 'is_active', 'created_at', 'profile', 'fingerprint')

    def get_profile(self, instance):
        request = self.context['request']
        profile_url = instance.profile.get_relative_rest_url()

        return request.build_absolute_uri(profile_url)
