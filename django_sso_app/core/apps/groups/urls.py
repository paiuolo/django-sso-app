from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from .views import GroupApiViewSet, GroupingApiViewSet


urlpatterns = [
    url(r'^$', GroupApiViewSet.as_view({'get': 'list'}), name="rest-list"),

    url(r'^groupings/$', GroupingApiViewSet.as_view({'get': 'list'}), name='rest-grouping-list'),
    url(r'^groupings/(?P<pk>\w+)/$', GroupingApiViewSet.as_view({'get': 'retrieve'}), name='rest-grouping-detail'),

    url(r'^(?P<name>.+)/$', GroupApiViewSet.as_view({'get': 'retrieve'}), name="rest-detail"),
]

urlpatterns = (format_suffix_patterns(urlpatterns), 'django_sso_app_group')
