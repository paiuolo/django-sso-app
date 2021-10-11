from django.contrib.auth.models import Group
from django.urls import reverse

from rest_framework import serializers


class PartialObjectSerializer(serializers.Serializer):
    _partial = serializers.SerializerMethodField(method_name='get_partial')

    def get_partial(self, obj):
        return True


class AbsoluteUrlSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField(method_name='get_absolute_rest_url')

    def get_absolute_rest_url(self, obj):
        if getattr(obj, 'pk', None) is not None:
            get_absolute_rest_url = getattr(obj, 'get_relative_rest_url', None)
            if get_absolute_rest_url is None:
                if obj.__class__ == Group:
                    request = self.context['request']
                    _rel_rest_url = reverse("django_sso_app_group:rest-detail", args=[obj.name])
                    return request.build_absolute_uri(_rel_rest_url)
                else:
                    raise NotImplementedError('Model must provide "get_relative_rest_url" method.')
            else:
                request = self.context['request']
                return request.build_absolute_uri(get_absolute_rest_url())


class UserRelatedSerializer(serializers.Serializer):
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        user = getattr(obj, 'user', None)
        if user is not None:
            profile = getattr(user, 'sso_app_profile', None)
            if profile is not None:
                request = self.context['request']
                reverse_url = profile.get_relative_rest_url()
                return request.build_absolute_uri(reverse_url)


class DeactivableSerializer(serializers.Serializer):
    is_active = serializers.BooleanField(required=False)


class PublicableSerializer(serializers.Serializer):
    is_public = serializers.BooleanField(required=False)


class TimespanSerializer(serializers.Serializer):
    started_at = serializers.DateTimeField(required=False)
    ended_at = serializers.DateTimeField(required=False)


class UpdatableSerializer(serializers.Serializer):
    updated_at = serializers.DateTimeField(required=False)


class CreatedAtSerializer(serializers.Serializer):
    created_at = serializers.DateTimeField(required=False)
