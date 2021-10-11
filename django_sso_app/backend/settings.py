from ..core.settings.common import *


# django-sso-app
DJANGO_SSO_APP_APIGATEWAY_HOST = env('DJANGO_SSO_APP_APIGATEWAY_HOST', default='http://kong')

DJANGO_SSO_APP_DJANGO_AUTHENTICATION_BACKENDS = [
    # login
    # 'allauth.account.auth_backends.AuthenticationBackend',  # overriden
    'django_sso_app.core.authentication.backends.login.DjangoSsoAppLoginAuthenticationBackend',

    # requests
    'django_sso_app.core.authentication.backends.DjangoSsoAppApiGatewayAuthenticationBackend',
    'django_sso_app.core.authentication.backends.DjangoSsoAppJwtAuthenticationBackend'
]

DJANGO_SSO_APP_DRF_AUTHENTICATION_CLASSES = ['django_sso_app.core.api.authentication.DjangoSsoApiAuthentication']

DJANGO_SSO_APP_BACKEND_CUSTOM_FRONTEND_APP = env('DJANGO_SSO_APP_BACKEND_CUSTOM_FRONTEND_APP', default=None)
if DJANGO_SSO_APP_BACKEND_CUSTOM_FRONTEND_APP is not None:
    DJANGO_SSO_APP_DJANGO_APPS = [
        DJANGO_SSO_APP_BACKEND_CUSTOM_FRONTEND_APP
    ] + DJANGO_SSO_APP_DJANGO_APPS

DJANGO_SSO_APP_USER_TYPES = env.list('DJANGO_SSO_APP_USER_TYPES', default=[])

# django
SESSION_COOKIE_SAMESITE = None  # Safari 12 and chrome cross site
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

_DJANGO_SSO_APP_APIGATEWAY_ENABLED = DJANGO_SSO_APP_SHAPE.find('apigateway') > -1
if _DJANGO_SSO_APP_APIGATEWAY_ENABLED:
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# allauth
# ------------------------------------------------------------------------------
ACCOUNT_ALLOW_REGISTRATION = True

# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'

# https://django-allauth.readthedocs.io/en/latest/configuration.html
# ! ACCOUNT_EMAIL_REQUIRED = 'email' in ACCOUNT_AUTHENTICATION_METHOD
ACCOUNT_EMAIL_REQUIRED = True
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_EMAIL_VERIFICATION = "mandatory" if ACCOUNT_EMAIL_REQUIRED else "optional"  # "none"

ACCOUNT_ADAPTER = "django_sso_app.core.adapter.AccountAdapter"
ACCOUNT_FORMS = {
    'signup': 'django_sso_app.core.forms.SignupForm',
    'login': 'django_sso_app.core.forms.LoginForm'
}

# https://django-allauth.readthedocs.iobackend/en/latest/configuration.html
# https://django-allauth.readthedocs.io/en/latest/configuration.html
# SOCIALACCOUNT_ADAPTER = "django_sso_app.backend.users.adapters.SocialAccountAdapter"

ACCOUNT_CONFIRM_EMAIL_ON_GET = True

# ! ACCOUNT_USERNAME_REQUIRED = 'username' in DJANGO_SSO_APP_USER_FIELDS
ACCOUNT_USERNAME_REQUIRED = False  # set to email by adapter

ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = False
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = '/'
ACCOUNT_SESSION_REMEMBER = False

# case insensitive username
ACCOUNT_PRESERVE_USERNAME_CASING = True

SOCIALACCOUNT_PROVIDERS = {}

if 'google' in DJANGO_SSO_APP_SOCIALACCOUNT_PROVIDERS:
    SOCIALACCOUNT_PROVIDERS['google'] = {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
