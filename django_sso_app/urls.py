from django.views.generic import TemplateView

from .core import app_settings

urlpatterns = []
api_urlpatterns = []
i18n_urlpatterns = []

app_name = 'django_sso_app'

if app_settings.BACKEND_ENABLED:
    from .backend.urls import django_sso_app_i18n_urlpatterns, django_sso_app_urlpatterns, \
                              django_sso_app_api_urlpatterns
    urlpatterns += django_sso_app_urlpatterns
    api_urlpatterns += django_sso_app_api_urlpatterns
    i18n_urlpatterns += django_sso_app_i18n_urlpatterns

    if app_settings.BACKEND_STANDALONE:
        from django.contrib.staticfiles.urls import staticfiles_urlpatterns
        urlpatterns += staticfiles_urlpatterns()
else:
    from .app.urls import django_sso_app_api_urlpatterns, django_sso_app_urlpatterns, \
                          django_sso_app_i18n_urlpatterns
    urlpatterns += django_sso_app_urlpatterns
    api_urlpatterns += django_sso_app_api_urlpatterns
    i18n_urlpatterns += django_sso_app_i18n_urlpatterns

if app_settings.BACKEND_ENABLED or app_settings.APP_ENABLED:
    from .core.mixins import WebpackBuiltTemplateViewMixin

    assert(WebpackBuiltTemplateViewMixin is not None)
else:
    class WebpackBuiltTemplateView(TemplateView):
        pass
