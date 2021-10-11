import logging

from django.contrib.auth import get_user_model

from rest_framework.authentication import SessionAuthentication

User = get_user_model()

logger = logging.getLogger('django_sso_app')


class DjangoSsoApiAuthentication(SessionAuthentication):
    """
    Returns authenticated user if set by authentication middleware
    """

    def enforce_csrf(self, request):
        """ SKIP Enforce CSRF validation for session based authentication. """
        pass
