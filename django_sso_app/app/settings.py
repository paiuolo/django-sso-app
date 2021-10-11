from ..core.settings.common import *


DJANGO_SSO_APP_DJANGO_AUTHENTICATION_BACKENDS = [
    # requests
    'django_sso_app.core.authentication.backends.DjangoSsoAppApiGatewayAuthenticationBackend',
    'django_sso_app.core.authentication.backends.DjangoSsoAppJwtAuthenticationBackend'
]
