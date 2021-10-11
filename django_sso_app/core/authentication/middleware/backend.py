import logging

from django.contrib import auth

from ...permissions import is_authenticated
from ...utils import check_user_can_login, get_session_key
from ... import app_settings
from ...apps.groups.utils import set_default_user_groups, set_default_profile_groups

from .base import DjangoSsoAppAuthenticationBaseMiddleware

logger = logging.getLogger('django_sso_app')


class DjangoSsoAppAuthenticationBackendMiddleware(DjangoSsoAppAuthenticationBaseMiddleware):
    def backend_process_request(self, request, request_jwt, decoded_jwt):
        user = getattr(request, 'user', None)

        if not is_authenticated(request.user):
            # We are seeing this user for the first time in this session, attempt
            # to authenticate the user.
            if app_settings.APIGATEWAY_ENABLED:
                consumer_custom_id = get_session_key(request, '__dssoa__apigateway__consumer_custom_id')

                user = auth.authenticate(request=request,
                                         consumer_custom_id=consumer_custom_id,
                                         encoded_jwt=request_jwt,
                                         decoded_jwt=decoded_jwt)
            else:
                user = auth.authenticate(request=request,
                                         encoded_jwt=request_jwt,
                                         decoded_jwt=decoded_jwt)

            # set request.user
            setattr(request, 'user', user)  # !!

        # further checks
        if is_authenticated(user):
            check_user_can_login(user)

            if app_settings.MANAGE_USER_GROUPS:
                # default groups check
                set_default_user_groups(user)
                set_default_profile_groups(user.sso_app_profile)

            logger.info('User "{}" authenticated successfully!'.format(user))
