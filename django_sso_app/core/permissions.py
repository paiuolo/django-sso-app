from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import permissions

from . import app_settings


def is_authenticated(user):
    return user is not None and user.is_authenticated


def is_django_staff(user):
    return user and (user.is_staff or user.is_superuser)


def is_staff(user):
    if user is not None:
        if is_django_staff(user):
            return True

        profile = getattr(user, 'sso_app_profile', None)
        if profile is not None:
            return profile.groups.filter(name__in=app_settings.STAFF_USER_GROUPS).count() > 0

    return False


def try_authenticate(username, email, password):
    credentials = username or email or None
    user = None

    if username is None and email is not None:
        credentials = 'email'
    if username is not None and email is None:
        credentials = 'username'

    if credentials is not None:
        user = authenticate(username=credentials, password=password)

    if user is not None:
        return user

    raise ObjectDoesNotExist('Check credentials.')


class OwnerPermission(permissions.IsAuthenticated):
    message = 'You must be the owner.'

    def has_object_permission(self, request, view, obj):
        if (getattr(request, 'user', None) is not None and request.user == obj):
            return True
        return False


class StaffPermission(permissions.IsAuthenticated):
    message = 'You must be a staff member.'

    def has_permission(self, request, view):
        if is_staff(request.user):
            return True
        return False


class NotDjangoStaffUserPermission(permissions.IsAuthenticated):
    message = 'Django staff users are disabled.'

    def has_permission(self, request, view):
        if is_django_staff(request.user):
            return False
        return True


class OwnerOrStaffPermission(permissions.IsAuthenticated):
    message = 'You must be the owner or a staff member.'

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user and (is_staff(user) or (user == getattr(obj, 'user', None))):
            return True
        return False


class PublicObjectOrOwnerOrStaffPermission(permissions.IsAuthenticated):

    def has_object_permission(self, request, view, obj):
        user = request.user
        user_is_staff = is_staff(user)

        if user_is_staff:
            return True

        is_public = getattr(obj, 'is_public', False)
        has_owner = getattr(obj, 'user', False)

        if (is_public and not has_owner) and not user_is_staff:
            return False

        if is_public:
            return True

        obj_user = getattr(obj, 'user', None)

        return obj_user == user
