import logging
# import inspect

from django.contrib import auth

from ...permissions import is_authenticated
from ...utils import get_session_key, check_user_can_login
from ... import app_settings
from ...apps.groups.utils import set_default_user_groups

from .base import DjangoSsoAppAuthenticationBaseMiddleware

logger = logging.getLogger('django_sso_app')


class DjangoSsoAppAuthenticationAppMiddleware(DjangoSsoAppAuthenticationBaseMiddleware):

    def app_process_request(self, request, request_jwt, decoded_jwt):
        user = getattr(request, 'user', None)

        if not is_authenticated(user):
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

            # set request user
            setattr(request, 'user', user)  # !!

        # further checks
        if is_authenticated(user):
            if app_settings.REPLICATE_PROFILE:
                check_user_can_login(user)
            else:
                if app_settings.SERVICE_SUBSCRIPTION_REQUIRED:
                    check_user_can_login(user, skip_profile_completion_checks=True)
                else:
                    check_user_can_login(user, skip_profile_completion_checks=True,
                                         skip_service_subscription_checks=True)

            if app_settings.MANAGE_USER_GROUPS:
                # default groups check
                set_default_user_groups(user)
                # update_profile_groups(user.sso_app_profile)  # profile groups are managed by backend

            logger.info('User "{}" authenticated successfully!'.format(user))
