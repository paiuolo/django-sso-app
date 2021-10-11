import logging

from rest_framework import serializers
from rest_framework.reverse import reverse

from ...serializers import AbsoluteUrlSerializer, PartialObjectSerializer
from ... import app_settings
from .models import Profile

logger = logging.getLogger('django_sso_app')


class ProfileSerializer(AbsoluteUrlSerializer):
    user = serializers.SerializerMethodField(required=False)
    sso_id = serializers.CharField()
    sso_rev = serializers.IntegerField()
    subscriptions = serializers.SerializerMethodField(required=False)

    ssn = serializers.CharField(required='ssn' in app_settings.REQUIRED_PROFILE_FIELDS)
    phone = serializers.CharField(required='phone' in app_settings.REQUIRED_PROFILE_FIELDS)

    first_name = serializers.CharField(required='first_name' in app_settings.REQUIRED_PROFILE_FIELDS)
    last_name = serializers.CharField(required='last_name' in app_settings.REQUIRED_PROFILE_FIELDS,
                                      allow_null=True,
                                      allow_blank=True)

    description = serializers.CharField(required='description' in app_settings.REQUIRED_PROFILE_FIELDS,
                                        allow_null=True, allow_blank=True)
    picture = serializers.CharField(required='picture' in app_settings.REQUIRED_PROFILE_FIELDS, allow_null=True)
    birthdate = serializers.DateField(required='birthdate' in app_settings.REQUIRED_PROFILE_FIELDS,
                                      allow_null=True)
    country_of_birth = serializers.CharField(required='country_of_birth' in app_settings.REQUIRED_PROFILE_FIELDS)

    latitude = serializers.FloatField(required='latitude' in app_settings.REQUIRED_PROFILE_FIELDS)
    longitude = serializers.FloatField(required='longitude' in app_settings.REQUIRED_PROFILE_FIELDS)

    country = serializers.CharField(required='country' in app_settings.REQUIRED_PROFILE_FIELDS)
    address = serializers.CharField(required='address' in app_settings.REQUIRED_PROFILE_FIELDS, allow_null=True)

    language = serializers.CharField(required='language' in app_settings.REQUIRED_PROFILE_FIELDS,
                                     allow_null=True)

    alias = serializers.CharField(required='alias' in app_settings.REQUIRED_PROFILE_FIELDS,
                                  allow_null=True)

    gender = serializers.CharField(required='gender' in app_settings.REQUIRED_PROFILE_FIELDS)

    groups = serializers.SerializerMethodField(required=False)

    meta = serializers.SerializerMethodField(required=False)

    is_incomplete = serializers.SerializerMethodField(required=False)
    required_fields = serializers.SerializerMethodField(required=False)
    completed_at = serializers.BooleanField(required=False)

    company_name = serializers.CharField(required='company_name' in app_settings.REQUIRED_PROFILE_FIELDS)

    # role = serializers.IntegerField(required='role' in app_settings.REQUIRED_PROFILE_FIELDS)

    class Meta:
        model = Profile
        read_only_fields = (
            'url',
            'created_at',
            'sso_id', 'sso_rev',
            'subscriptions',
            'is_unsubscribed',
            'username', 'email',
            'user',
            'groups',
            'meta',
            'is_incomplete', 'required_fields', 'completed_at') + app_settings.USER_FIELDS
        fields = read_only_fields + app_settings.PROFILE_FIELDS

    def get_groups(self, instance):
        groups = list(instance.groups.values_list('name', flat=True))

        return groups

    def get_subscriptions(self, instance):
        serialized = []
        if app_settings.BACKEND_ENABLED:
            for el in instance.subscriptions.all():
                serialized.append({
                    'service_url': el.service.service_url,
                    'is_unsubscribed': getattr(el, 'is_unsubscribed', False)
                })
        return serialized

    def get_is_incomplete(self, instance):
        return instance.is_incomplete

    def get_required_fields(self, instance):
        serialized = []
        if app_settings.BACKEND_ENABLED:
            if instance.is_incomplete:
                for field in app_settings.REQUIRED_PROFILE_FIELDS:
                    if getattr(instance, field, None) in (None, ''):
                        serialized.append(field)

        return serialized

    def get_absolute_rest_url(self, obj):
        if getattr(obj, 'id', None) is not None:
            request = self.context['request']
            reverse_url = reverse('django_sso_app_profile:rest-detail', args=[obj.sso_id])

            return request.build_absolute_uri(reverse_url)

    def get_user(self, instance):
        try:
            user = instance.user
            request = self.context['request']
            return request.build_absolute_uri(user.get_relative_rest_url())
        except:
            logger.warning('No profile.user url for {}.'.format(instance))

    def get_meta(self, instance):
        return instance.meta


class ProfilePublicSerializer(ProfileSerializer, PartialObjectSerializer):

    class Meta:
        model = Profile
        read_only_fields = (
            'url',
            'sso_id',
            'created_at', 'username', 'picture',
            'country',
            '_partial')
        fields = read_only_fields


class ProfileUnsubscriptionSerializer(serializers.Serializer):
    password = serializers.CharField()
