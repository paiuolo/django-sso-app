import logging


from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.forms import ValidationError
from django.http import Http404
# from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
# from django.views.decorators.cache import cache_page
# from django.db.models import Q
from django.core.exceptions import SuspiciousOperation

from django_filters.rest_framework import DjangoFilterBackend

from allauth.account.utils import filter_users_by_username, filter_users_by_email

from rest_framework import generics
from rest_framework import mixins
from rest_framework import status
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (CheckUserExistenceSerializer,
                          UserSerializer, NewUserSerializer,
                          UserRevisionSerializer)

from ...apps.emails.models import EmailAddress
from ...permissions import StaffPermission
from ...permissions import is_staff, is_django_staff
from ...utils import invalidate_cookie, get_session_key
from ...views import DjangoSsoAppBaseViewMixin
from ... import app_settings
from .filters import UserFilter

User = get_user_model()

logger = logging.getLogger('django_sso_app')


class CheckUserExistenceApiView(APIView):
    """
    Retrieve a "condensed" user instance {"id": ".."} by either "username" or "email" as query params.
    """

    permission_classes = (permissions.AllowAny, )

    def get_object(self, login=None, username=None, email=None):
        try:
            if login is not None:
                #! NOQA
                email_users = filter_users_by_email(login)
                if len(email_users):
                    return email_users[0]

                username_users = filter_users_by_username(login)
                if len(username_users):
                    return username_users[0]

            elif username is None and email is not None:
                users = filter_users_by_email(email)
                if len(users):
                    return users[0]

            elif username is not None and email is None:
                users = filter_users_by_username(username)
                if len(users):
                    return users[0]

            raise User.DoesNotExist('Either login username or email must be set.')

        except (User.DoesNotExist, EmailAddress.DoesNotExist):
            return None

    def get(self, *args, **kwargs):
        login = self.request.query_params.get('login', self.request.GET.get('login', None))
        username = self.request.query_params.get('username', None)
        email = self.request.query_params.get('email', None)

        found = False
        if login is not None or username is not None or email is not None:
            item = self.get_object(login, username, email)
            found = item is not None

        if not found:
            raise Http404

        serializer = CheckUserExistenceSerializer(item)

        return Response(serializer.data)


class UserApiViewSet(mixins.ListModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet,
                     DjangoSsoAppBaseViewMixin):
    """
    User api viewset
    """

    lookup_field = 'sso_app_profile__sso_id'
    # serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = UserFilter

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return NewUserSerializer
        else:
            return UserSerializer

    def get_queryset(self):
        requesting_user = self.request.user
        queryset = User.objects.filter(is_superuser=False, is_active=True)

        if is_staff(requesting_user):
            return queryset
        else:
            return queryset.filter(pk=requesting_user.pk)

    def get_object(self, *args, **kwargs):
        sso_id = self.kwargs.get('sso_id')

        try:
            user = User.objects.get(sso_app_profile__sso_id=sso_id)
            self.check_object_permissions(self.request, user)
            return user
        except User.DoesNotExist:
            raise Http404

    def list(self, request, *args, **kwargs):
        """
        List users
        """
        logger.info('List users')

        return super(UserApiViewSet, self).list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        Create user
        """
        logger.info('Creating user')

        if not is_staff(request.user):
            msg = 'Non staff user "{}" tried to create new user'.format(request.user)
            logger.warning(msg)

            raise(SuspiciousOperation(msg))

        return super(UserApiViewSet, self).create(request, *args, **kwargs)

    def partial_update(self, request, sso_id, *args, **kwargs):
        logger.info('Updating user')

        try:
            user = self.get_object()
            response = super(UserApiViewSet, self).partial_update(request, sso_id, *args, **kwargs)

        except (IntegrityError, ValidationError) as e:
            logger.exception('partial_update')

            logger.info('User {0} tried to update email with already registered one'.format(request.user))

            response = Response(_('Email already registered.'), status=status.HTTP_409_CONFLICT)

        response_status_code = response.status_code
        logger.debug('Partial_update status code is {}, {}'.format(response_status_code, request.data))

        if response_status_code == 200:
            requesting_user = request.user
            is_same_user = requesting_user == user

            if is_same_user and not is_django_staff(requesting_user):

                # must login again if password updated
                if get_session_key(request, '__dssoa__user_password_updated', False):
                    logger.info('User {0} updated password and must login again'.format(requesting_user))

                    invalidate_cookie(response, app_settings.JWT_COOKIE_NAME)
                else:
                    self.update_response_jwt(user, response)

        return response


class UserRevisionsApiView(mixins.ListModelMixin,
                           viewsets.GenericViewSet):
    """
    User revisions entrypoint
    """

    queryset = User.objects.filter(is_superuser=False, is_staff=False).order_by('id')
    serializer_class = UserRevisionSerializer
    permission_classes = (StaffPermission,)

    def list(self, request, *args, **kwargs):
        """
        List users revisions
        """
        logger.info('List users revisions')
        return super(UserRevisionsApiView, self).list(request, *args, **kwargs)


class UserDetailApiView(generics.RetrieveAPIView):
    """
    User detail entrypoint
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_object(self, *args, **kwargs):
        user = getattr(self.request, 'user', None)
        return user
