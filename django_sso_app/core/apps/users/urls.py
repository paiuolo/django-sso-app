from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from .views import (CheckUserExistenceApiView,
                    UserApiViewSet,
                    UserRevisionsApiView,
                    UserDetailApiView)

_urlpatterns = [
    url(r'^$', UserApiViewSet.as_view({'get': 'list', 'post': 'create'}), name='rest-list'),

    url(r'^(?P<sso_id>[-_\w]+)/$',
        UserApiViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update'},
                               name='rest-detail'),
        name='rest-detail'),
]

extra_urlpatterns = (format_suffix_patterns([
                         url(r'^user/$', UserDetailApiView.as_view(), name="user_detail"),
                         url(r'^check-user/$', CheckUserExistenceApiView.as_view(), name="check_user_existence"),
                         url(r'^get-revisions/$', UserRevisionsApiView.as_view({'get': 'list'}), name="get_users_revisions")]),
                     'django_sso_app_user_extra')

urlpatterns = (format_suffix_patterns(_urlpatterns), 'django_sso_app_user')
