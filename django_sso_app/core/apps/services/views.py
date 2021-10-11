import logging

from django.contrib.auth import get_user_model
from django.http import Http404
from rest_framework import mixins
from rest_framework import permissions
from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response

from .models import Service, Subscription
from .serializers import SubscriptionSerializer, ServiceSerializer, ServiceSubscriptionSerializer
from ..profiles.models import Profile
from ...permissions import is_staff, is_authenticated
from ...tokens.utils import get_request_jwt
from ..devices.utils import renew_response_jwt

logger = logging.getLogger('django_sso_app')
User = get_user_model()


class ServiceApiViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    """
    Service API viewset
    """

    serializer_class = ServiceSerializer
    permission_classes = (permissions.AllowAny, )

    def get_queryset(self):
        return Service.objects.filter(is_public=True, is_active=True)


class ServiceSubscriptionApiViewSet(mixins.CreateModelMixin,
                                    viewsets.GenericViewSet):
    """
    ServiceSubscription API viewset
    """

    serializer_class = ServiceSubscriptionSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        return Service.objects.filter(is_public=True, is_active=True)

    def subscribe(self, request, pk, *args, **kwargs):
        logger.info('subscribing')

        requesting_user = request.user
        service = Service.objects.get(id=pk)

        if service is None:
            raise Http404

        profile = None

        if is_staff(requesting_user):
            serializer = ServiceSubscriptionSerializer(data=request.data)

            if serializer.is_valid():
                user_sso_id = serializer.validated_data.get('sso_id', None)
                if user_sso_id is not None:
                    profile = Profile.objects.filter(sso_id=user_sso_id).first()
        else:
            profile = requesting_user.sso_app_profile

        if profile is None:
            raise Http404

        if profile.subscriptions.filter(service=service).count() > 0:
            return Response('Already subscribed.', status=status.HTTP_409_CONFLICT)

        _subscription, subscription_created = service.subscribe(profile, update_rev=True)

        if subscription_created:
            response = Response('Successfully subscribed.', status=status.HTTP_201_CREATED)
        else:
            return Response('Service subscription error.', status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        received_jwt = get_request_jwt(request)
        from_browser_as_same_user = received_jwt is not None

        if from_browser_as_same_user:  # From browser as same user
            logger.info(
                'From browser as same user "{}"'.format(requesting_user))
            logger.info('updating JWT for {}'.format(requesting_user))

            renew_response_jwt(received_jwt, requesting_user, request, response)

        return response

    def unsubscribe(self, request, pk, *args, **kwargs):
        logger.info('unsubscribing')

        requesting_user = request.user
        service = Service.objects.get(id=pk)

        if service is None:
            raise Http404

        profile = None

        if is_staff(requesting_user):
            serializer = ServiceSubscriptionSerializer(data=request.data)

            if serializer.is_valid():
                user_sso_id = serializer.validated_data.get('sso_id', None)
                if user_sso_id is not None:
                    profile = Profile.objects.filter(sso_id=user_sso_id).first()
        else:
            profile = requesting_user.sso_app_profile

        if profile is None:
            raise Http404

        logger.info('"{}" unsubscribing from "{}"'.format(profile, service))

        _subscription, subscription_disabled = service.unsubscribe(profile, update_rev=True)

        if subscription_disabled:
            response = Response('Successfully unsubscribed.', status=status.HTTP_200_OK)
            received_jwt = get_request_jwt(request)
            from_browser_as_same_user = received_jwt is not None

            if from_browser_as_same_user:  # From browser as same user
                logger.info(
                    'From browser as same user "{}"'.format(requesting_user))
                logger.info('updating JWT for {}'.format(requesting_user))

                renew_response_jwt(received_jwt, requesting_user, request, response)

            return response
        else:
            response = Response('Can not unsubsribe.', status=status.HTTP_400_BAD_REQUEST)

            return response


class SubscriptionApiViewSet(mixins.ListModelMixin,
                             mixins.RetrieveModelMixin,
                             viewsets.GenericViewSet):
    """
    Subscription API viewset
    """

    serializer_class = SubscriptionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        requesting_user = self.request.user

        if is_authenticated(requesting_user):
            if is_staff(requesting_user):
                return Subscription.objects.all()
            else:
                return Subscription.objects.filter(profile=requesting_user.sso_app_profile)
        else:
            return Subscription.objects.none()
