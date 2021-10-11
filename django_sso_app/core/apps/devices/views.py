import logging

from django.contrib.auth import get_user_model
from rest_framework import mixins
from rest_framework import permissions
from rest_framework import viewsets

from .models import Device
from .serializers import DeviceSerializer
from ...permissions import is_staff, is_authenticated, OwnerOrStaffPermission

User = get_user_model()

logger = logging.getLogger('django_sso_app')


class DeviceApiViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.DestroyModelMixin,
                       viewsets.GenericViewSet):
    """
    Device API viewset
    """

    serializer_class = DeviceSerializer
    permission_classes = (OwnerOrStaffPermission,)

    def get_queryset(self):
        requesting_user = self.request.user

        if is_authenticated(requesting_user):
            if is_staff(requesting_user):
                return Device.objects.all()
            else:
                return Device.objects.filter(profile=requesting_user.sso_app_profile)

        return Device.objects.none()
