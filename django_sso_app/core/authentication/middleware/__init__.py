import logging

from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import smart_str

from jwt.exceptions import InvalidSignatureError

from ... import app_settings
from ...utils import set_session_key, get_session_key, invalidate_cookie
from ...permissions import is_authenticated, is_django_staff
from ...exceptions import RequestHasValidJwtWithNoDeviceAssociated, ServiceSubscriptionRequiredException, ProfileIncompleteException
from ...tokens.utils import get_request_jwt, jwt_decode

from .backend import DjangoSsoAppAuthenticationBackendMiddleware
from .app import DjangoSsoAppAuthenticationAppMiddleware

logger = logging.getLogger('django_sso_app')

SSO_ID_JWT_KEY = 'sso_id'
FINGERPRINT_JWT_KEY = 'fp'


class DjangoSsoAppAuthenticationMiddleware(DjangoSsoAppAuthenticationBackendMiddleware,
                                           DjangoSsoAppAuthenticationAppMiddleware):
    """
    See django.contrib.auth.middleware.RemoteUserMiddleware.
    """

    def process_request(self, request):
        # AuthenticationMiddleware is required so that request.user exists.
        if not hasattr(request, 'user'):
            raise ImproperlyConfigured(
                "SSO middleware requires the authentication middleware to be"
                " installed.  Edit your MIDDLEWARE setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the SsoMiddleware class.")

        request_path = request.path
        request_method = request.method
        request_ip = request.META.get('REMOTE_ADDR', None)
        requesting_user = request.user

        logger.info('--> "{}" request "{}" path "{}" method "{}" user "{}"'.format(request_ip,
                                                                                   id(request),
                                                                                   request_path,
                                                                                   request_method,
                                                                                   requesting_user))

        if is_authenticated(requesting_user):

            if is_django_staff(requesting_user):
                logger.info('Skipping django staff user "{}"'.format(requesting_user))
                #  >= 1.10 has is_authenticated as parameter
                # If a staff user is already authenticated, we don't need to
                # continue

                return

            elif self._is_admin_path(request):
                logger.warning('Non staff user "{}" called admin path'.format(requesting_user))

                self._remove_invalid_user(request)
                self._clear_response_jwt(request)

                return

        # saving request info
        set_session_key(request, '__dssoa__request_ip', request_ip)
        set_session_key(request, '__dssoa__requesting_user', requesting_user)

        """
        if self.request_path.startswith('/api/v1/passepartout'):
            logger.info('is passepartout path')
            # set_session_key(request, '__dssoa__is_passepartout_path', True)
        """

        try:
            request_jwt = get_request_jwt(request, encoded=False)

            if request_jwt is None:
                logger.info('No JWT in request, skipping')

                return

            else:
                # decoding request JWT
                request_device, decoded_jwt = jwt_decode(request_jwt, verify=True)

        except KeyError:
            logger.exception('Malformed JWT "{}"'.format(request_jwt))

            self._remove_invalid_user(request)
            self._clear_response_jwt(request)

            return

        except InvalidSignatureError:
            logger.warning('Invalid JWT signature "{}"'.format(request_jwt))

            self._remove_invalid_user(request)
            self._clear_response_jwt(request)

            return

        except RequestHasValidJwtWithNoDeviceAssociated:
            logger.warning('RequestHasValidJwtWithNoDeviceAssociated "{}"'.format(request_jwt))

            self._remove_invalid_user(request)
            self._clear_response_jwt(request)

            return

        except Exception:
            logger.exception('Generic middleware exception "{}"'.format(request_jwt))

            self._remove_invalid_user(request)
            self._clear_response_jwt(request)

            return

        else:
            # caching device fingerprint
            request_device_fingerprint = decoded_jwt[FINGERPRINT_JWT_KEY]
            logger.debug('Caching request fingerprint: {}'.format(request_device_fingerprint))
            set_session_key(request, '__dssoa__device__fingerprint', request_device_fingerprint)

        apigateway_enabled = app_settings.APIGATEWAY_ENABLED
        request_jwt_sso_id = decoded_jwt[SSO_ID_JWT_KEY]

        if apigateway_enabled:
            consumer_custom_id = request.META.get(self.consumer_id_header, None)
            consumer_is_anonymous_header = request.META.get(self.anonymous_consumer_header, None)

            if consumer_is_anonymous_header is not None and \
                    consumer_is_anonymous_header == self.anonymous_consumer_header_value:
                consumer_is_anonymous = True
            else:
                if consumer_custom_id is None:
                    consumer_is_anonymous = True
                else:
                    if consumer_custom_id in self.anonymous_consumer_custom_ids:
                        consumer_is_anonymous = True
                    else:
                        consumer_is_anonymous = False

            if consumer_is_anonymous:
                # If anonymous consumer header specified or consumer custom id header don't exist
                # or consumer custom_id is one of anonymous consumer custom_ids
                # then remove any existing authenticated user and return (leaving request.user set to
                # AnonymousUser by the AuthenticationMiddleware).

                logger.info('User is anonymous')

                self._remove_invalid_user(request)

                return

            else:
                sso_id = consumer_custom_id

                set_session_key(request, '__dssoa__apigateway__consumer_custom_id', consumer_custom_id)

        else:
            sso_id = request_jwt_sso_id

        # If the user is already authenticated and that user is active and the
        # one we are getting passed in the headers, then the correct user is
        # already persisted in the session and we don't need to continue.
        if is_authenticated(requesting_user):
            # double check sso_id equality between received jwt and sso_app_profile
            if smart_str(requesting_user.sso_id) != sso_id:

                # An authenticated user is associated with the request, but
                # it does not match the authorized user in the header.
                logger.warning('credentials and request_user sso_id differs! "{}" "{}"'.format(sso_id,
                                                                                               requesting_user.sso_id))

                self._remove_invalid_user(request)
                self._clear_response_jwt(request)

                return

        try:
            # authentication
            if app_settings.BACKEND_ENABLED:
                self.backend_process_request(request, request_jwt, decoded_jwt)
            else:
                self.app_process_request(request, request_jwt, decoded_jwt)

        except ProfileIncompleteException as e:
            if self._request_path_is_disabled_for_incomplete_users(request):
                logger.info('User must complete profile')
                set_session_key(request, '__dssoa__redirect', e.response)

        except ServiceSubscriptionRequiredException as e:
            if self._request_path_is_disabled_for_users_to_subscribe(request):
                logger.info('User must subscribe service')
                set_session_key(request, '__dssoa__redirect', e.response)

        except Exception as e:
            logger.exception('Generic middleware backend exception "{}"'.format(e))

            self._remove_invalid_user(request)

            return

    @staticmethod
    def _process_response(request, response):
        redirect = get_session_key(request, '__dssoa__redirect', None)

        if redirect is not None:
            return redirect

        # invalidate JWT cookie on response (if required)
        if get_session_key(request, '__dssoa__clear_response_jwt', False):
            invalidate_cookie(response, app_settings.JWT_COOKIE_NAME)

        return response

    def process_response(self, request, response):
        # getting request info
        requesting_user = getattr(request, 'user', get_session_key(request, '__dssoa__requesting_user', None))
        request_ip = get_session_key(request, '__dssoa__request_ip')

        user_logged_in = get_session_key(request, '__dssoa__logged_in', False)  # !!
        user_logged_out = get_session_key(request, '__dssoa__logged_out', False)
        request_fp = get_session_key(request, '__dssoa__device__fingerprint', None)

        logger.debug('login: {} - logout: {} - FP: {}'.format(user_logged_in, user_logged_out, request_fp))

        response = self._process_response(request, response)

        logger.info('<-- "{}" request "{}" user "{}" path "{}" method "{}" ({})'.format(request_ip,
                                                                                        id(request),
                                                                                        requesting_user,
                                                                                        request.path,
                                                                                        request.method,
                                                                                        response.status_code))

        return response
