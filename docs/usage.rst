=====
Usage
=====

To use Django SSO App in a project, add it to your `INSTALLED_APPS`:

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
