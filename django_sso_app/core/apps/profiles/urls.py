from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from .views import ProfileApiViewSet, ProfileDetailApiView


_base_urlpatterns = [
    url(r'^$', ProfileApiViewSet.as_view({'get': 'list'}), name='rest-list'),

    url(r'^(?P<sso_id>[-_\w]+)/$', ProfileApiViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update'}),
        name="rest-detail"),
]

_urlpatterns = _base_urlpatterns

extra_urlpatterns = (format_suffix_patterns([
                         url(r'^profile/$', ProfileDetailApiView.as_view(), name="detail")]),
                     'django_sso_app_profile_extra')

base_urlpatterns = (format_suffix_patterns(_base_urlpatterns), 'django_sso_app_profile')
urlpatterns = (format_suffix_patterns(_urlpatterns), 'django_sso_app_profile')
