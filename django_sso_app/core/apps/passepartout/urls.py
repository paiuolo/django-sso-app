from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from .views import passepartout_login_view

_urlpatterns = [
    url(r'^login/(?P<token>\w+)/$',
        passepartout_login_view,
        name='login')
]

urlpatterns = (format_suffix_patterns(_urlpatterns), 'django_sso_app_passepartout')
