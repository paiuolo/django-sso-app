import logging

from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import pre_save, post_save

from ....utils import set_session_key
from ....tokens.utils import jwt_encode
from ....functions import get_random_string
from ....permissions import is_django_staff
from ...profiles.models import Profile

from .... import app_settings

from ..models import Device
from ..utils import get_session_key, get_or_create_request_device, remove_all_profile_devices, remove_profile_device

logger = logging.getLogger('django_sso_app')


# profile

@receiver(post_save, sender=Profile)
def post_profile_saved(sender, instance, created, **kwargs):
    if kwargs['raw']:
        # https://github.com/django/django/commit/18a2fb19074ce6789639b62710c279a711dabf97
        return

    profile = instance
    user = instance.user

    if not is_django_staff(user):
        if not created:  # if instance.pk:
            logger.debug('Profile "{}" post_save signal'.format(profile))

            rev_updated = getattr(profile, '__rev_updated', False)

            if rev_updated:
                logger.info('Rev updated, removing all user devices for Profile "{}"'.format(profile))

                remove_all_profile_devices(profile)


# device

@receiver(pre_save, sender=Device)
def pre_device_save(sender, instance, **kwargs):
    if not app_settings.APIGATEWAY_ENABLED:
        user = instance.profile.user
        device = instance

        if not is_django_staff(user):
            logger.debug('Skip creating api gateway JWT for Device "{}"'.format(device))

            device.apigw_jwt_id = None
            device.apigw_jwt_key = None
            device.apigw_jwt_secret = device.apigw_jwt_secret or get_random_string(32)


# login

@receiver(user_logged_in)
def create_profile_device_on_login(sender, request, user, **kwargs):
    """
    Sent when a user logs in successfully.
    Assign device and JWT token to request object.

    Arguments sent with this signal:

    sender
        The class of the user that just logged in.
    request
        The current HttpRequest instance.
    user
        The user instance that just logged in.

    """

    logger.debug('devices user_logged_in signal for user "{}"'.format(user))

    set_session_key(request, '__dssoa__logged_in', True)

    if not is_django_staff(user):
        device = get_or_create_request_device(request)
        token = jwt_encode(device.get_jwt_payload(), device.apigw_jwt_secret)

        set_session_key(request, '__dssoa__device', device)
        set_session_key(request, '__dssoa__jwt_token', token)

        logger.info('User Logged in, request has device "{}"'.format(device))


# logout

@receiver(user_logged_out)
def delete_profile_devices_on_logout(sender, request, user, **kwargs):
    """
    Sent when a user logs out successfully.

    Arguments sent with this signal:


Sent when the logout method is called.

    sender
        As above: the class of the user that just logged out or ``None``
        if the user was not authenticated.

    request
        The current :class:`~django.http.HttpRequest` instance.

    user
        The user instance that just logged out or ``None`` if the
        user was not authenticated.

    """
    logger.debug('devices user_logged_out signal for "{}"'.format(user))

    if user is not None:
        set_session_key(request, '__dssoa__logged_out', True)

        request_device_fingerprint = get_session_key(request, '__dssoa__device__fingerprint', None)

        if app_settings.LOGOUT_DELETES_ALL_PROFILE_DEVICES:
            deleted_devices = remove_all_profile_devices(user.get_sso_app_profile())
        else:
            if request_device_fingerprint is not None:
                request_device = Device.objects.filter(profile=user.get_sso_app_profile(),
                                                       fingerprint=request_device_fingerprint).first()
                if request_device is not None:
                    deleted_devices = remove_profile_device(request_device)
                else:
                    logger.warning('Request device not found')
                    deleted_devices = 0
            else:
                deleted_devices = 0

        logger.info('({}) devices deleted for user "{}"'.format(deleted_devices, user))
