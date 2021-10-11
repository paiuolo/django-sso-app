import logging

from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model

from rest_framework import authentication

from .. import app_settings
from ..exceptions import AuthenticationFailed, InvalidToken
from .utils import get_request_jwt_header, jwt_decode

User = get_user_model()

logger = logging.getLogger('django_sso_app')


class JWTAuthentication(authentication.BaseAuthentication):
    """
    An authentication plugin that authenticates requests through a JSON web
    token provided in a request header.
    """
    www_authenticate_realm = 'api'

    def authenticate(self, request):
        logger.info('Authenticating')

        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)

        return self.get_user(validated_token), None

    def authenticate_header(self, request):
        return '{0} realm="{1}"'.format(
            app_settings.AUTH_HEADER_TYPES[0],
            self.www_authenticate_realm,
        )

    def get_header(self, request):
        """
        Extracts the header containing the JSON web token from the given
        request.
        """
        return get_request_jwt_header(request, encoded=True)

    def get_raw_token(self, header):
        """
        Extracts an unvalidated JSON web token from the given "Authorization"
        header value.
        """
        parts = header.split()
        if len(parts) == 0:
            # Empty AUTHORIZATION header sent
            return None

        if parts[0] not in app_settings.AUTH_HEADER_TYPE_BYTES:
            # Assume the header does not contain a JSON web token
            return None
        if len(parts) != 2:
            raise AuthenticationFailed(
                _('Authorization header must contain two space-delimited values'),
                code='bad_authorization_header',
            )

        return parts[1]

    def get_validated_token(self, raw_token):
        """
        Validates an encoded JSON web token and returns a validated token
        wrapper object.
        """
        messages = []

        try:
            _device, decoded_jwt = jwt_decode(raw_token, verify=True)

            return decoded_jwt

        except Exception as e:
            logger.info('error deconding token')
            messages.append('{}'.format(e))

        raise InvalidToken({
            'detail': _('Given token not valid for any token type'),
            'messages': messages,
        })

    def get_user(self, validated_token):
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            sso_id = validated_token[app_settings.USER_ID_CLAIM]
        except KeyError:
            raise InvalidToken(_('Token contained no recognizable user identification'))

        try:
            user = User.objects.get(**{app_settings.USER_ID_FIELD: sso_id})
        except User.DoesNotExist:
            raise AuthenticationFailed(_('User not found'), code='user_not_found')

        if not user.is_active:
            raise AuthenticationFailed(_('User is inactive'), code='user_inactive')

        return user
