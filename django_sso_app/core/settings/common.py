"""
django envs:
    SESSION_ENGINE, SESSION_COOKIE_NAME, SESSION_COOKIE_PATH, \
    SESSION_COOKIE_DOMAIN, SESSION_SAVE_EVERY_REQUEST, SESSION_COOKIE_SECURE, SESSION_COOKIE_HTTPONLY, \
    SESSION_COOKIE_SAMESITE
"""

import environ

env = environ.Env()

# common
DEBUG = env.bool("DJANGO_DEBUG", default=True)
APP_DOMAIN = env("APP_DOMAIN", default="localhost:8000")
COOKIE_DOMAIN = env("COOKIE_DOMAIN", default=APP_DOMAIN.split(':')[0])
ACCOUNT_DEFAULT_HTTP_PROTOCOL = env("ACCOUNT_DEFAULT_HTTP_PROTOCOL", default='http' if DEBUG else 'https')
I18N_PATH_ENABLED = env.bool('I18N_PATH_ENABLED', default=False)

REDIS_ENABLED = env.bool('REDIS_ENABLED', default=False)

# django-sso-app
DJANGO_SSO_APP_SOCIALACCOUNT_PROVIDERS = env.list('DJANGO_SSO_APP_SOCIALACCOUNT_PROVIDERS', default=[])

BACKEND_SHAPES = ('backend_standalone',
                  'backend_only',
                  'backend_only_apigateway',
                  'backend_app',
                  'backend_app_apigateway')
APP_SHAPES = ('app',
              'app_persistence',
              'app_apigateway',
              'app_persistence_apigateway')

AVAILABLE_SHAPES = BACKEND_SHAPES + APP_SHAPES

DJANGO_SSO_APP_SHAPE = env('DJANGO_SSO_APP_SHAPE', default='backend_only')

DJANGO_SSO_APP_BASE_DJANGO_APPS = [
    'django_sso_app',
]

DJANGO_SSO_APP_DJANGO_APPS = [
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    'rest_framework.authtoken',

    'django_countries',

    'treebeard'

] + DJANGO_SSO_APP_BASE_DJANGO_APPS

if 'google' in DJANGO_SSO_APP_SOCIALACCOUNT_PROVIDERS:
    DJANGO_SSO_APP_DJANGO_APPS += [
        'allauth.socialaccount.providers.google',
    ]

# django
# SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

COUNTRIES_FIRST = [
    'IT',
]
