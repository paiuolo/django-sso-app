from django.conf.urls import url
from django.urls import include
from django.views.generic.base import RedirectView

from ..core.apps.groups.urls import urlpatterns as groups_urls
from ..core.apps.users.urls import urlpatterns as users_urls
from ..core.apps.users.urls import extra_urlpatterns as users_extra_urls
from ..core.apps.profiles.urls import base_urlpatterns as profiles_urls
from ..core.apps.profiles.urls import extra_urlpatterns as profiles_extra_urls
from ..core import app_settings

from .views import AppLoginView, AppSignupView, AppLogoutView


django_sso_app_profile_urlpatterns = [
    url(r'^profile/$', RedirectView.as_view(url=app_settings.REMOTE_PROFILE_VIEW_URL, permanent=False),
        name='profile'),
    url(r'^profile/update/$', RedirectView.as_view(url=app_settings.REMOTE_PROFILE_UPDATE_URL, permanent=False),
        name='profile.update'),
    url(r'^profile/complete/$', RedirectView.as_view(url=app_settings.REMOTE_PROFILE_COMPLETE_URL, permanent=False),
        name='profile.complete'),
]

django_sso_app_i18n_urlpatterns = django_sso_app_profile_urlpatterns

django_sso_app_urlpatterns = [
    url(r'^logout/$', AppLogoutView.as_view(), name='account_logout'),
    url(r'^login/$', AppLoginView.as_view(), name='account_login'),
    url(r'^signup/$', AppSignupView.as_view(), name='account_signup'),
    url(r'^email/$', RedirectView.as_view(url=app_settings.REMOTE_EMAIL_URL, permanent=False), name='account_email'),

    url(r"^password/change/$", RedirectView.as_view(url=app_settings.BACKEND_URL + '/password/change/', permanent=False),
        name='account_change_password'),
    url(r"^password/reset/$", RedirectView.as_view(url=app_settings.BACKEND_URL + '/password/reset/', permanent=False),
        name='account_reset_password'),
    url(r"^email/$", RedirectView.as_view(url=app_settings.BACKEND_URL + '/email/', permanent=False),
        name='account_email'),
]

django_sso_app_api_urlpatterns = [
    url(r'^api/v1/auth/groups/', include(groups_urls)),
    url(r'^api/v1/auth/users/', include(users_urls)),
    url(r'^api/v1/auth/profiles/', include(profiles_urls)),
] + [
    url(r'^api/v1/auth/', include(users_extra_urls)),
    url(r'^api/v1/auth/', include(profiles_extra_urls)),
]
