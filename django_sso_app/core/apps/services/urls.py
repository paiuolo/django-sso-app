from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from .views import ServiceApiViewSet, SubscriptionApiViewSet, ServiceSubscriptionApiViewSet


_service__urlpatterns = [
    url(r'^$',
        ServiceApiViewSet.as_view({'get': 'list'}),
        name='rest-list'),
    url(r'^(?P<pk>\d+)/$',
        ServiceApiViewSet.as_view({'get': 'retrieve'}),
        name='rest-detail'),

    url(r'^(?P<pk>\d+)/subscribe/$',
        ServiceSubscriptionApiViewSet.as_view({'post': 'subscribe'}),
        name='rest-subscription'),

    url(r'^(?P<pk>\d+)/unsubscribe/$',
        ServiceSubscriptionApiViewSet.as_view({'post': 'unsubscribe'}),
        name='rest-unsubscription'),
]

_subscription_urlpatterns = [
    url(r'^subscriptions/$',
        SubscriptionApiViewSet.as_view({'get': 'list'}),
        name='rest-subscription-list'),

    url(r'^subscriptions/(?P<pk>\d+)/$',
        SubscriptionApiViewSet.as_view({'get': 'retrieve'}),
        name='rest-subscription-detail'),
]

service_urlpatterns = format_suffix_patterns(_service__urlpatterns)
subscription_urlpatterns = format_suffix_patterns(_subscription_urlpatterns)

urlpatterns = (service_urlpatterns + subscription_urlpatterns, 'django_sso_app_service')
