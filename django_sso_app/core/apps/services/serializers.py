import logging

from rest_framework.reverse import reverse
from rest_framework import serializers

from ...serializers import AbsoluteUrlSerializer
from .models import Service, Subscription

logger = logging.getLogger('django_sso_app')


class ServiceSerializer(AbsoluteUrlSerializer):
    is_subscribed = serializers.SerializerMethodField(required=False)
    is_unsubscribed = serializers.SerializerMethodField(required=False)
    tos = serializers.SerializerMethodField(required=False)
    subscribe = serializers.SerializerMethodField(required=False)
    unsubscribe = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Service
        read_only_fields = ('url', 'id', 'picture', 'is_subscribed', 'is_unsubscribed')
        fields = read_only_fields + ('service_url', 'name',
                                     'cookie_domain',
                                     'redirect_wait',
                                     'is_public',
                                     'tos',
                                     'subscription_required',
                                     'subscribe', 'unsubscribe')  # 'groups'

    def get_is_subscribed(self, instance):
        request = self.context.get("request")
        user = request.user
        if user is None or user.is_anonymous:
            return False

        subscription = request.user.sso_app_profile.subscriptions.filter(service=instance).first()
        if subscription is not None:
            return subscription.is_subscribed

        return False

    def get_is_unsubscribed(self, instance):
        request = self.context.get("request")
        user = request.user

        if user is None or user.is_anonymous:
            return False

        subscription = request.user.sso_app_profile.subscriptions.filter(service=instance).first()
        if subscription is not None:
            return subscription.is_unsubscribed

        return False

    def get_tos(self, instance):
        request = self.context.get('request')
        language = request.LANGUAGE_CODE
        tos = instance.get_tos(language)

        if tos is None:
            instance.get_tos('en')
        if tos is None:
            return None

        return tos.text

    def get_subscribe(self, instance):
        request = self.context['request']

        return request.build_absolute_uri(reverse('django_sso_app_service:rest-subscription',
                                          kwargs={'pk': instance.id}))

    def get_unsubscribe(self, instance):
        request = self.context['request']

        return request.build_absolute_uri(reverse('django_sso_app_service:rest-unsubscription',
                                          kwargs={'pk': instance.id}))


class ServiceSubscriptionSerializer(serializers.Serializer):
    sso_id = serializers.CharField(required=False)


class SubscriptionSerializer(AbsoluteUrlSerializer):
    service = ServiceSerializer()
    profile = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Subscription
        fields = ('url', 'id', 'service', 'created_at', 'is_unsubscribed', 'profile', 'is_public')

    def get_profile(self, instance):
        request = self.context['request']
        profile_url = instance.profile.get_relative_rest_url()

        return request.build_absolute_uri(profile_url)
