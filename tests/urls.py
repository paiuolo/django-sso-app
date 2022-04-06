# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from django.conf import settings
from django.conf.urls import url
from django.urls import include
from django.contrib import admin
from django.contrib.auth.decorators import login_required

from django.utils import timezone
from django.views.i18n import JavaScriptCatalog
from django.views.decorators.http import last_modified

from django_sso_app.urls import (urlpatterns as django_sso_app__urlpatterns,
                                 api_urlpatterns as django_sso_app__api_urlpatterns,
                                 i18n_urlpatterns as django_sso_app_i18n_urlpatterns)

from .views import home

last_modified_date = timezone.now()
js_info_dict = {}


urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^jsi18n/$', last_modified(lambda req, **kw: last_modified_date)(JavaScriptCatalog.as_view()), js_info_dict,
        name='javascript-catalog'),
]

if settings.DJANGO_DEBUG_TOOLBAR_ENABLED:
    urlpatterns.append(url(r'^__debug__/', include('debug_toolbar.urls')))

urlpatterns += [
    url(r'^$', login_required(home), name='home'),
]

urlpatterns += django_sso_app__urlpatterns
urlpatterns += django_sso_app__api_urlpatterns
urlpatterns += django_sso_app_i18n_urlpatterns
