import logging

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from ...apps.users.utils import fetch_remote_user, create_local_user_from_remote_backend, \
                              update_local_user_from_remote_backend, create_local_user_from_jwt, \
                              create_local_user_from_apigateway_headers

from ...apps.profiles.models import Profile
from ... import app_settings


logger = logging.getLogger('django_sso_app')
User = get_user_model()


class DjangoSsoAppAppBaseAuthenticationBackend(ModelBackend):

    def try_replicate_user(self, request, sso_id, encoded_jwt, decoded_jwt):
        logger.debug('try_replicate_user')

        if app_settings.REPLICATE_PROFILE:
            logger.info('Replicate user with sso_id "{}" from remote backend'.format(sso_id))

            # create local profile from SSO
            backend_user = fetch_remote_user(sso_id=sso_id, encoded_jwt=encoded_jwt)
            #backend_user_profile = backend_user['profile']

            user = create_local_user_from_remote_backend(backend_user)

            #if backend_user_profile.get('is_incomplete', False):
            #    redirect_to_profile_complete(user)

        else:
            user = None

        return user

    def try_update_user(self, sso_id, user, user_profile, encoded_jwt, decoded_jwt):
        logger.debug('try_update_user')

        rev_changed = user_profile.sso_rev < decoded_jwt['sso_rev']

        if rev_changed:
            if rev_changed:
                logger.info('Rev changed from "{}" to "{}" for user "{}", updating ...'
                            .format(user_profile.sso_rev, decoded_jwt['sso_rev'],
                                    user))

            # local profile updated from django_sso_app instance, do not update sso_rev
            setattr(user, '__dssoa__creating', True)

            remote_user_object = fetch_remote_user(sso_id=sso_id, encoded_jwt=encoded_jwt)
            user = update_local_user_from_remote_backend(user, remote_user_object)

            logger.info('{} updated with latest data from BACKEND'.format(user))

            setattr(user, '__dssoa__creating', False)

        else:
            logger.info('Nothing changed for user "{}"'.format(user))

        return user


class DjangoSsoAppApiGatewayAppAuthenticationBackend(DjangoSsoAppAppBaseAuthenticationBackend):
    """
    Authenticates by request CONSUMER_CUSTOM_ID header
    """

    def try_replicate_user(self, request, sso_id, encoded_jwt, decoded_jwt):
        user = super(DjangoSsoAppApiGatewayAppAuthenticationBackend, self).try_replicate_user(request, sso_id,
                                                                                              encoded_jwt, decoded_jwt)

        if user is None:
            logger.info('Creating user from headers')

            user = create_local_user_from_apigateway_headers(request)

        return user

    def app_authenticate(self, request, consumer_custom_id, encoded_jwt, decoded_jwt):
        logger.info('APP authenticating by apigateway consumer {}'.format(consumer_custom_id))

        try:
            sso_id = consumer_custom_id
            profile = Profile.objects.get(sso_id=sso_id)
            user = profile.user

        except ObjectDoesNotExist:
            logger.info('No profile with id "{}"'.format(sso_id))
            try:
                user = self.try_replicate_user(request, sso_id, encoded_jwt, decoded_jwt)

            except Exception as e:
                logger.exception('Can not replicate user: {}'.format(e))
                raise

        else:
            if app_settings.REPLICATE_PROFILE:
                logger.debug('Should replicate profile')

                if decoded_jwt is None:
                    logger.warning('decoded_jwt not set')
                    return

                user = self.try_update_user(sso_id, user, profile, encoded_jwt, decoded_jwt)

        return user


class DjangoSsoAppJwtAppAuthenticationBackend(DjangoSsoAppAppBaseAuthenticationBackend):
    """
    Authenticates by request jwt
    """

    def try_replicate_user(self, request, sso_id, encoded_jwt, decoded_jwt):

        user = super(DjangoSsoAppJwtAppAuthenticationBackend, self).try_replicate_user(request,
                                                                                       sso_id, encoded_jwt, decoded_jwt)

        if user is None:
            # create local profile from jwt
            logger.info('Replicating user with sso_id "{}" from JWT'.format(sso_id))

            user = create_local_user_from_jwt(decoded_jwt)

        return user

    def app_authenticate(self, request, encoded_jwt, decoded_jwt):
        logger.info('backend authenticating by request jwt')

        if encoded_jwt is None or decoded_jwt is None:
            logger.debug('request jwt not set, skipping authentication')

            return

        try:
            sso_id = decoded_jwt['sso_id']
            profile = Profile.objects.get(sso_id=sso_id)
            user = profile.user

            if app_settings.REPLICATE_PROFILE:
                logger.debug('try_update_user "{}" jwt consumer "{}"'.format(sso_id, sso_id))

                user = self.try_update_user(sso_id, user, profile, encoded_jwt, decoded_jwt)

            else:
                # just updates user groups
                logger.debug('Do not replicate profile')

        except ObjectDoesNotExist:
            try:
                user = self.try_replicate_user(request, sso_id, encoded_jwt, decoded_jwt)

            except Exception:
                logger.exception('Can not replicate remote user')
                raise

        else:
            if app_settings.REPLICATE_PROFILE:
                logger.debug('Should replicate profile')

                if decoded_jwt is None:
                    logger.warning('decoded_jwt not set')
                    raise

                user = self.try_update_user(sso_id, user, profile, encoded_jwt, decoded_jwt)

        return user
