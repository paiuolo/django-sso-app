from django.apps import AppConfig


class DjangoSsoAppConfig(AppConfig):
    name = 'django_sso_app'
    label = 'django_sso_app'

    def ready(self):
        try:
            import django_sso_app.core.apps.api_gateway.signals  # noqa F401
            import django_sso_app.core.apps.emails.signals  # noqa F401
            import django_sso_app.core.apps.devices.signals  # noqa F401
            import django_sso_app.core.apps.groups.signals  # noqa F401
            import django_sso_app.core.apps.passepartout.signals  # noqa F401
            import django_sso_app.core.apps.profiles.signals  # noqa F401
            import django_sso_app.core.apps.services.signals  # noqa F401
            import django_sso_app.core.apps.status.signals  # noqa F401
            import django_sso_app.core.apps.users.signals  # noqa F401
            import django_sso_app.core.apps.events.signals  # noqa F401

        except ImportError:
            pass
