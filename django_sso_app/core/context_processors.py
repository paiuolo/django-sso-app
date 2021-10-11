from django.conf import settings

from . import app_settings


def django_sso_app_context(request):
    return {
        "sso_cookie_domain": app_settings.JWT_COOKIE_NAME,

        "APP_DOMAIN": settings.APP_DOMAIN,
        "COOKIE_DOMAIN": app_settings.COOKIE_DOMAIN,
        "I18N_PATH_ENABLED": settings.I18N_PATH_ENABLED,

        "DJANGO_SSO_APP_BACKEND_ENABLED": app_settings.BACKEND_ENABLED,
        "DJANGO_SSO_APP_APIGATEWAY_ENABLED": app_settings.APIGATEWAY_ENABLED,
        "DJANGO_SSO_APP_JWT_COOKIE_NAME": app_settings.JWT_COOKIE_NAME,
        "DJANGO_SSO_APP_BACKEND_HAS_CUSTOM_FRONTEND_APP": app_settings.BACKEND_HAS_CUSTOM_FRONTEND_APP,
        "DJANGO_SSO_APP_PROFILE_FIELDS": app_settings.PROFILE_FIELDS,
        "DJANGO_SSO_APP_BACKEND_SIGNUP_MUST_FILL_PROFILE": app_settings.BACKEND_SIGNUP_MUST_FILL_PROFILE,
    }
