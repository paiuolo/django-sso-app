import logging

import jwt

from ...tokens.utils import jwt_decode, jwt_encode
from ...utils import get_session_key, set_session_key, logger, set_cookie, get_random_fingerprint
from ...tokens.utils import get_request_jwt
from ...exceptions import RequestHasValidJwtWithNoDeviceAssociated
from ... import app_settings

logger = logging.getLogger('django_sso_app')


def add_profile_device(profile, fingerprint, secret=None):
    secret = secret or app_settings.TOKENS_JWT_SECRET

    logger.info(
        'Adding User Device for profile "{}" with fingerprint "{}" and secret "{}"'.format(profile,
                                                                                           fingerprint,
                                                                                           secret))

    device = profile.devices.model.objects.create(profile=profile, fingerprint=fingerprint, apigw_jwt_secret=secret)

    logger.debug('device "{}" created with key "{}" secret "{}" and fingerprint "{}"'.format(device,
                                                                                             device.apigw_jwt_key,
                                                                                             device.apigw_jwt_secret,
                                                                                             device.fingerprint))
    return device


def remove_profile_device(device):
    logger.info('Deleting Device "{}"'.format(device))

    device.delete()

    return 1


def remove_all_profile_devices(profile):
    logger.info('Removing All Profile Devices for "{}"'.format(profile))

    removed = 0
    for device in profile.devices.all():
        removed += remove_profile_device(device)

    return removed


def get_or_create_request_device(request):
    device = get_session_key(request, '__dssoa__device', None)

    if device is None:
        logger.debug('no previous device')
        fingerprint = get_session_key(request, '__dssoa__device__fingerprint')  # set by views

        if fingerprint is None:
            logger.debug('received empty fingerprint, checking JWT')

            raw_token = get_request_jwt(request)

            if raw_token is None:
                fingerprint = get_random_fingerprint(request)  # 'undefined'
            else:
                try:
                    device, verified_payload = jwt_decode(raw_token, verify=True)

                except RequestHasValidJwtWithNoDeviceAssociated:
                    logger.warning('no device associated to request token "{}"'.format(raw_token))
                    raise
                else:
                    fingerprint = verified_payload['fp']

        if device is None:
            user = request.user
            profile = user.sso_app_profile

            logger.info(
                'Request has no device, getting profile "{}" device with fingerprint "{}"'.format(profile,
                                                                                                  fingerprint))

            device = profile.devices.filter(fingerprint=fingerprint).first()

            if device is None:
                logger.debug('profile has no device with fingerprint "{}"'.format(fingerprint))
                device = add_profile_device(user.get_sso_app_profile(), fingerprint)
            else:
                logger.debug('fingerprint "{}" had device'.format(fingerprint))

        else:
            logger.debug('request has device "{}"'.format(device))

    else:
        logger.info(
            'request already has device "{}"'.format(device))

    assert device is not None

    set_session_key(request, '__dssoa__device', device)
    set_session_key(request, '__dssoa__device__fingerprint', device.fingerprint)

    return device


def renew_response_jwt(received_jwt, user, request, response):
    logger.debug('renewing response jwt for "{}"'.format(user))

    unverified_payload = jwt.decode(received_jwt, None, False)
    jwt_fingerprint = unverified_payload['fp']

    logger.info('Updating response JWT for User {0} with fingerprint {1}'.format(request.user, jwt_fingerprint))

    # creates new actual_device
    device = add_profile_device(user.get_sso_app_profile(), jwt_fingerprint)
    token = jwt_encode(device.get_jwt_payload(), device.apigw_jwt_secret)

    # max_age = 365 * 24 * 60 * 60  #one year
    # expires = datetime.datetime.strftime(datetime.datetime.utcnow() + \
    #     datetime.timedelta(seconds=max_age), "%a, %d-%b-%Y %H:%M:%S GMT")

    set_cookie(response, app_settings.JWT_COOKIE_NAME, token)
