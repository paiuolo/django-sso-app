import logging

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from ...apps.profiles.models import Profile

logger = logging.getLogger('django_sso_app')
User = get_user_model()


class DjangoSsoAppApiGatewayBackendAuthenticationBackend(ModelBackend):
    """
    Authenticates by request CONSUMER_CUSTOM_ID header
    """

    backend_path = 'django_sso_app.core.authentication.backends.DjangoSsoAppApiGatewayAuthenticationBackend'

    def backend_authenticate(self, request, consumer_custom_id, encoded_jwt, decoded_jwt):
        logger.info('BACKEND authenticating by apigateway consumer {}'.format(consumer_custom_id))

        if consumer_custom_id is None:
            logger.debug('consumer_custom_id not set, skipping authentication')

            return

        try:
            sso_id = consumer_custom_id
            profile = Profile.objects.get(sso_id=sso_id)
            user = profile.user

        except ObjectDoesNotExist:
            logger.debug('user with apigateway consumer_custom_id "{}" does not exists'.format(consumer_custom_id))

            return

        else:
            logger.debug('user with apigateway consumer_custom_id "{}" exists'.format(consumer_custom_id))

            # allauth logic
            setattr(user, 'backend', self.backend_path)

        return user


class DjangoSsoAppJwtBackendAuthenticationBackend(ModelBackend):
    """
    Authenticates by request jwt
    """

    backend_path = 'django_sso_app.core.authentication.backends.DjangoSsoAppApiGatewayAuthenticationBackend'

    def backend_authenticate(self, request, encoded_jwt, decoded_jwt):
        logger.info('BACKEND authenticating by request jwt')

        try:
            sso_id = decoded_jwt['sso_id']
            profile = Profile.objects.get(sso_id=sso_id)
            user = profile.user

        except ObjectDoesNotExist:
            logger.debug('user with sso_id "{}" does not exists'.format(sso_id))
            return

        else:
            logger.debug('user with sso_id "{}" exists'.format(sso_id))

            # allauth logic
            setattr(user, 'backend', self.backend_path)

        return user
