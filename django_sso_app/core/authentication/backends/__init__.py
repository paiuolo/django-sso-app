import logging

from ... import app_settings

from .backend import DjangoSsoAppApiGatewayBackendAuthenticationBackend, DjangoSsoAppJwtBackendAuthenticationBackend
from .app import DjangoSsoAppApiGatewayAppAuthenticationBackend, DjangoSsoAppJwtAppAuthenticationBackend

logger = logging.getLogger('django_sso_app')


class DjangoSsoAppApiGatewayAuthenticationBackend(DjangoSsoAppApiGatewayBackendAuthenticationBackend,
                                                  DjangoSsoAppApiGatewayAppAuthenticationBackend):

    """
    Authenticates by request CONSUMER_CUSTOM_ID header

    See django.contrib.auth.backends.RemoteUserBackend.

    """

    backend_path = 'django_sso_app.core.authentication.backends.DjangoSsoAppApiGatewayAuthenticationBackend'

    def authenticate(self, request, consumer_custom_id, encoded_jwt, decoded_jwt):
        if app_settings.BACKEND_ENABLED:
            return self.backend_authenticate(request,
                                             consumer_custom_id,
                                             encoded_jwt,
                                             decoded_jwt)
        else:
            return self.app_authenticate(request,
                                         consumer_custom_id,
                                         encoded_jwt,
                                         decoded_jwt)


class DjangoSsoAppJwtAuthenticationBackend(DjangoSsoAppJwtBackendAuthenticationBackend,
                                           DjangoSsoAppJwtAppAuthenticationBackend):
    """
    Authenticates by request jwt

    Example JWT:

        {
          "sso_id": "<uuid>",
          "sso_rev": 0,
          "id": 1,
          "fp": "b28493a6a29a5a38973a8a3e3abe7f34",
          "iss": "nxhnkMPKcpRWaTKwNOvGcLcs5MHJINOg"
        }

    """

    backend_path = 'django_sso_app.core.authentication.backends.DjangoSsoAppApiGatewayAuthenticationBackend'

    def authenticate(self, request, encoded_jwt, decoded_jwt):
        if app_settings.BACKEND_ENABLED:
            return self.backend_authenticate(request,
                                             encoded_jwt,
                                             decoded_jwt)
        else:
            return self.app_authenticate(request,
                                         encoded_jwt,
                                         decoded_jwt)
