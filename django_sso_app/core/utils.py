import os
import logging
import datetime
import binascii
from random import seed, randint
import base64

from django.core.management.utils import get_random_secret_key
from django.utils.http import urlencode
from django.http import HttpResponseRedirect
from django.conf import settings

from .tokens.utils import logger
from .exceptions import (ProfileIncompleteException, DectivatedUserException, UnsubscribedUserException,
                         DjangoStaffUsersCanNotLoginException, ServiceSubscriptionRequiredException,
                         AnonymousUserException)
from .permissions import is_authenticated, is_django_staff
from . import app_settings

logger = logging.getLogger('django_sso_app')
# initializing seed
SEED = int(base64.b16encode(bytes(get_random_secret_key(), 'utf-8')), 16)
seed(SEED)

JWT_COOKIE_SECURE = not settings.DEBUG


def set_cookie(response, key, value, days_expire=None, secure=JWT_COOKIE_SECURE):
    """
    Sets response auth cookie

    :param response:
    :param key:
    :param value:
    :param days_expire:
    :param secure:
    :return:
    """

    if days_expire is None:
        max_age = app_settings.COOKIE_AGE  # django default
    else:
        max_age = days_expire * 24 * 60 * 60

    expires = datetime.datetime.strftime(datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age),
                                         "%a, %d-%b-%Y %H:%M:%S GMT")

    response.set_cookie(key, value, max_age=None, expires=expires, path='/',
                        domain=app_settings.COOKIE_DOMAIN,
                        secure=secure,
                        httponly=app_settings.COOKIE_HTTPONLY)

    # samesite None cookie patch
    # replaced by "same_site" middleware
    # if app_settings.SAME_SITE_COOKIE_NONE:
    #    response.cookies[key]['samesite'] = 'None'


def invalidate_cookie(response, key):
    """
    Sets response auth cookie to 'Null'

    :param response:
    :param key:
    :return:
    """
    response.set_cookie(key, '', max_age=None, expires='Thu, 01 Jan 1970 00:00:01 GMT', path='/',
                        domain=app_settings.COOKIE_DOMAIN, secure=None, httponly=False)


def set_session_key(request, key, value):
    """
    Sets django sessions request key
    :param request:
    :param key:
    :param value:
    :return:
    """

    #request.session[key] = value

    setattr(request, key, value)


def get_session_key(request, key, default=None):
    """
    Gets django sessions request key
    :param request:
    :param key:
    :param default:
    :return:
    """

    #return request.session.get(key, default)

    return getattr(request, key, default)


def redirect_to_profile_complete(user):
    if app_settings.BACKEND_ENABLED:
        url = app_settings.PROFILE_COMPLETE_URL
    else:
        _qs = urlencode({'next': app_settings.SERVICE_URL})
        url = '{}{}?{}'.format(app_settings.BACKEND_URL, app_settings.PROFILE_COMPLETE_URL, _qs)

    logger.info('User {} must complete profile,'
                ' redirecting to {} ...'
                .format(user, url))

    response = HttpResponseRedirect(redirect_to=url)

    raise ProfileIncompleteException(response)


def redirect_to_service_subscription(user, service_url=None):
    if app_settings.BACKEND_ENABLED:
        url = app_settings.LOGIN_URL
    else:
        if service_url is None:
            service_url = app_settings.SERVICE_URL

        _qs = urlencode({'next': service_url})
        url = '{}{}?{}'.format(app_settings.BACKEND_URL, app_settings.LOGIN_URL, _qs)

    logger.info('User {} must agree to the Terms of Service,'
                ' redirecting to {} ...'
                .format(user, url))

    response = HttpResponseRedirect(redirect_to=url)

    raise ServiceSubscriptionRequiredException(response)


def check_user_can_login(user, skip_profile_completion_checks=False, skip_service_subscription_checks=False):
    """
    Check user login ability
    :param user:
    :param skip_profile_completion_checks:
    :param skip_service_subscription_checks:
    :return:
    """
    if is_authenticated(user):
        if is_django_staff(user):
            raise DjangoStaffUsersCanNotLoginException()
        elif not user.is_active:
            raise DectivatedUserException()
        else:
            if user.sso_app_profile.is_unsubscribed:
                raise UnsubscribedUserException()
            else:
                if not skip_profile_completion_checks:
                    if user.sso_app_profile.is_incomplete:
                        redirect_to_profile_complete(user)

                if not skip_service_subscription_checks:
                    if user.sso_app_profile.must_subscribe:
                        redirect_to_service_subscription(user)
    else:
        raise AnonymousUserException()


def get_random_token(length=4):
    """
    Returns random token
    :param length:
    :return:
    """
    start = randint(0, 4095 - length)
    end = start + length

    return binascii.hexlify(os.urandom(2048)).decode("utf-8")[start:end]


def get_random_fingerprint(request):
    """
    Returns random fingerprint
    :param request:
    :return:
    """
    return 'random_{}_{}'.format(id(request), get_random_token(8))
