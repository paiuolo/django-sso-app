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
        'django_sso_app.apps.DjangoSsoAppConfig',
        ...
    )

Add Django SSO App's URL patterns:

.. code-block:: python

    from django_sso_app import urls as django_sso_app_urls


    urlpatterns = [
        ...
        url(r'^', include(django_sso_app_urls)),
        ...
    ]

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
