import logging
import jwt

from rest_framework import HTTP_HEADER_ENCODING

from ..exceptions import RequestHasValidJwtWithNoDeviceAssociated
from .. import app_settings

_TOKEN_PREFIXES = tuple(map(lambda x: '{} '.format(x), app_settings.AUTH_HEADER_TYPES))
logger = logging.getLogger('django_sso_app')


def get_request_jwt_header(request, encoded=True):
    """
    Extracts the header containing the JSON web token from the given
    request.
    """
    jwt_header = request.META.get('HTTP_AUTHORIZATION', None)

    if encoded and isinstance(jwt_header, str):
        # Work around django test client oddness
        jwt_header = jwt_header.encode(HTTP_HEADER_ENCODING)

    logger.debug('header JWT "{}"'.format(jwt_header))
    return jwt_header


def get_request_jwt_cookie(request, encoded=True):
    """
    Extracts the header containing the JSON web token from the given
    request.
    """
    jwt_cookie = request.COOKIES.get(app_settings.JWT_COOKIE_NAME, None)

    if encoded and isinstance(jwt_cookie, str):
        # Work around django test client oddness
        jwt_cookie = jwt_cookie.encode(HTTP_HEADER_ENCODING)

    logger.debug('cookie JWT "{}"'.format(jwt_cookie))
    return jwt_cookie


def get_request_jwt(request, encoded=False):
    request_jwt = request_jwt_header = get_request_jwt_header(request, False)

    if request_jwt_header is None:
        request_jwt = get_request_jwt_cookie(request, False)

    else:
        _found = None
        for token_prefix in _TOKEN_PREFIXES:
            if request_jwt_header.find(token_prefix) != -1:
                _found = token_prefix
                break

        if _found is not None:
            logger.debug('request jwt found')
            request_jwt = request_jwt.replace(_found, '')
        else:
            logger.debug('"{}" absent on "{}"'.format(_TOKEN_PREFIXES, request_jwt_header))
            return

    if request_jwt is not None and encoded and isinstance(request_jwt, str):
        # Work around django test client oddness
        request_jwt = request_jwt.encode(HTTP_HEADER_ENCODING)

    return request_jwt


def get_request_jwt_fingerprint(request):
    received_jwt = get_request_jwt(request)
    if received_jwt is None:
        raise KeyError('No token specified')

    unverified_payload = jwt.decode(received_jwt, None, False)
    return unverified_payload.get('fp')


def jwt_decode_handler(token, secret_key, issuer, verify=True):
    # get user from token, BEFORE verification, to get user secret key

    unverified_payload = jwt.decode(token, None, False)

    if not verify:
        return unverified_payload

    options = {
        'verify_exp': False,
    }

    return jwt.decode(
        token,
        secret_key,
        verify,
        options=options,
        #leeway=api_settings.JWT_LEEWAY,
        #audience=api_settings.JWT_AUDIENCE,
        issuer=issuer,  # api_settings.APIJWT_ISSUER,
        algorithms=[app_settings.JWT_ALGORITHM]
    )


def jwt_encode_handler(payload, secret_key):
    return jwt.encode(
        payload,
        secret_key,
        app_settings.JWT_ALGORITHM
    ).decode('utf-8')


def jwt_encode(payload, secret):
    return jwt_encode_handler(payload, secret)


def jwt_decode(raw_token, verify=True):
    if app_settings.BACKEND_ENABLED:
        from ..apps.devices.models import Device

        logger.debug('decode backend jwt')
        unverified_payload = jwt.decode(raw_token, None, False)

        try:
            device_id = unverified_payload['id']
            fingerprint = unverified_payload['fp']
            device = Device.objects.get(id=device_id,
                                        fingerprint=fingerprint)

        except Device.DoesNotExist:
            logger.warning('no device with "{}:{}" found in db, raising'.format(device_id, fingerprint))

            raise RequestHasValidJwtWithNoDeviceAssociated(device_id)

        return device, jwt_decode_handler(raw_token, device.apigw_jwt_secret, device.apigw_jwt_key, verify)

    else:
        logger.debug('decode app jwt')

        if app_settings.APIGATEWAY_ENABLED:
            return None, jwt_decode_handler(raw_token, app_settings.TOKENS_JWT_SECRET, None, False)
        else:
            return None, jwt_decode_handler(raw_token, app_settings.TOKENS_JWT_SECRET, None, verify)
