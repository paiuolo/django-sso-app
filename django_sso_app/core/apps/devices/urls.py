from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from .views import DeviceApiViewSet


_urlpatterns = [
    url(r'^$', DeviceApiViewSet.as_view({'get': 'list'}), name='rest-list'),
    url(r'^(?P<pk>\d+)/$', DeviceApiViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}),
        name="rest-detail"),
]

urlpatterns = (format_suffix_patterns(_urlpatterns), 'django_sso_app_device')
