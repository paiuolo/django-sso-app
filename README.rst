=============================
Django SSO App
=============================

.. image:: https://badge.fury.io/py/django-sso-app.svg
    :target: https://badge.fury.io/py/django-sso-app

.. image:: https://travis-ci.org/paiuolo/django-sso-app.svg?branch=master
    :target: https://travis-ci.org/paiuolo/django-sso-app

.. image:: https://codecov.io/gh/paiuolo/django-sso-app/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/paiuolo/django-sso-app

Django user profiles management app

Documentation
-------------

The full documentation is at https://django-sso-app.readthedocs.io.

Quickstart
----------

Install Django SSO App::

    pip install django-sso-app

Add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...

        'django.contrib.sites',

        'rest_framework',
        'rest_framework.authtoken',

        'django_sso_app',

        'allauth',
        'allauth.account',
        'allauth.socialaccount',

        'django_countries',
        'django_filters',

        'treebeard',

        ...
    )

Setup settings.py:

.. code-block:: python

    MIDDLEWARE = [
        ...

        'django.contrib.auth.middleware.AuthenticationMiddleware',  # required by django-sso-app
        'django_sso_app.core.authentication.middleware.DjangoSsoAppAuthenticationMiddleware',  # django-sso-app

        ...
    ]

    ...

    LOGIN_URL = '/login/'
    LOGIN_REDIRECT_URL = '/'

    SITE_ID = 1

Add Django SSO App's URL patterns:

.. code-block:: python

    from django.utils import timezone
    from django.views.i18n import JavaScriptCatalog
    from django.views.decorators.http import last_modified

    from django_sso_app.urls import (urlpatterns as django_sso_app__urlpatterns,
                                     api_urlpatterns as django_sso_app__api_urlpatterns,
                                     i18n_urlpatterns as django_sso_app_i18n_urlpatterns)


    last_modified_date = timezone.now()
    js_info_dict = {}

    urlpatterns = [
        ...

        url(r'^jsi18n/$', last_modified(lambda req, **kw: last_modified_date)(JavaScriptCatalog.as_view()), js_info_dict,
        name='javascript-catalog'),

        ...
    ]

    urlpatterns += django_sso_app__urlpatterns
    urlpatterns += django_sso_app__api_urlpatterns
    urlpatterns += django_sso_app_i18n_urlpatterns

Features
--------

* TODO

Running Tests
-------------

Does the code actually work?

::

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install tox
    (myenv) $ tox


Development commands
---------------------

::

    pip install -r requirements_dev.txt
    invoke -l


Credits
-------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
