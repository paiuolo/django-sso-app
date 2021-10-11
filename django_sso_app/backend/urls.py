from django.conf.urls import url
from django.urls import include
from django.contrib.auth.decorators import login_required
#from django.conf import settings
#from django.views.generic.base import RedirectView

from ..core.apps.users.urls import urlpatterns as users_urls
from ..core.apps.users.urls import extra_urlpatterns as users_extra_urls
from ..core.apps.groups.urls import urlpatterns as groups_urls
from ..core.apps.profiles.urls import urlpatterns as profiles_urls
from ..core.apps.profiles.urls import extra_urlpatterns as profiles_extra_urls
from ..core.apps.profiles.views import ProfileView, ProfileUpdateView, ProfileCompleteView
from ..core.apps.services.urls import urlpatterns as services_urls
from ..core.apps.devices.urls import urlpatterns as devices_urls
from ..core.apps.passepartout.urls import urlpatterns as passepartout_urls

from ..core.urls import allauth_urlpatterns, allauth_i18n_urlpatterns
from ..core.api.urls import allauth_api_urlpatterns

django_sso_app_profile_urlpatterns = [
    url(r'^profile/$', login_required(ProfileView.as_view()), name='profile'),
    url(r'^profile/update/$', login_required(ProfileUpdateView.as_view()), name='profile.update'),
    url(r'^profile/complete/$', login_required(ProfileCompleteView.as_view()), name='profile.complete'),
]
django_sso_app_i18n_urlpatterns = django_sso_app_profile_urlpatterns + allauth_i18n_urlpatterns
django_sso_app_urlpatterns = allauth_urlpatterns
django_sso_app_api_urlpatterns = allauth_api_urlpatterns

django_sso_app_api_urlpatterns += [
    url(r'^api/v1/auth/groups/', include(groups_urls)),
    url(r'^api/v1/auth/users/', include(users_urls)),
    url(r'^api/v1/auth/profiles/', include(profiles_urls)),

    url(r'^api/v1/auth/devices/', include(devices_urls)),
    url(r'^api/v1/auth/services/', include(services_urls)),
    url(r'^api/v1/auth/passepartout/', include(passepartout_urls)),

    # url('^api/v1/jwt/refresh/?', TokenRefreshView.as_view(), name='token_refresh'),
    # url('^api/v1/jwt/verify/?', TokenVerifyView.as_view(), name='token_verify'),
] + [
    url(r'^api/v1/auth/', include(users_extra_urls)),
    url(r'^api/v1/auth/', include(profiles_extra_urls)),
]
