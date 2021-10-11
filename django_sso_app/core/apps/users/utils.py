import json
import logging

import requests

from django.db import transaction
from django.utils.encoding import smart_str
from django.contrib.auth import get_user_model

from ... import app_settings
from ..emails.models import EmailAddress
from ..profiles.utils import update_profile
from ..api_gateway.functions import get_apigateway_profile_groups_from_header

logger = logging.getLogger('django_sso_app')


def fetch_remote_user(sso_id, encoded_jwt=None):
    """
    Fetches user model from remote django-sso-app backend
    :param sso_id:
    :param encoded_jwt:
    :return:
    """
    logger.info("Getting SSO profile for ID {} ...".format(sso_id))

    if encoded_jwt is None:
        logger.debug('Using Token')
        headers = {
            "Authorization": "Token {}".format(app_settings.BACKEND_STAFF_TOKEN)
        }
    else:
        logger.debug('Using JWT')
        headers = {
            "Authorization": "Bearer {}".format(encoded_jwt)
        }

    url = app_settings.REMOTE_USER_URL.format(sso_id=sso_id) + '?with_password=true'

    response = requests.get(url=url, headers=headers, timeout=10, verify=False)
    response.raise_for_status()
    sso_user = response.json()

    logger.info("Retrieved SSO profile for ID {}".format(sso_id))

    return sso_user


def update_user(user, update_object, commit=True):
    logger.info('Try update user fields for "{}"'.format(user))

    for f in app_settings.USER_FIELDS + ('password', 'is_active', 'date_joined'):
        if hasattr(user, f):
            new_val = update_object.get(f, None)
            if new_val is not None:
                setattr(user, f, new_val)
                logger.debug('user field updated "{}":"{}"'.format(f, new_val if f != 'password' else '*'))

    if commit:
        user.save()

    return user


def check_remote_user_existence_by_username(username):
    logger.info('Checking with SSO Backend if user {} already exists ...'
                .format(smart_str(username)))

    url = app_settings.BACKEND_USERS_CHECK_URL
    params = {
        'username': username
    }
    response = requests.get(url=url, params=params, timeout=10, verify=False)
    response.raise_for_status()

    if response.status_code == requests.codes.NOT_FOUND:
        logger.info('User {} does NOT exist'.format(smart_str(username)))

        return None

    sso_id = json.loads(response.text).get('sso_id', None)

    logger.info('User {} already exists with SSO ID {}'
                .format(smart_str(username), sso_id))

    return sso_id


def check_remote_user_existence_by_email(email):
    logger.info('Checking with SSO if a user with email {} already exists ...'
                .format(smart_str(email)))

    url = app_settings.REMOTE_USERS_CHECK_URL
    params = {
        'email': email
    }
    response = requests.get(url=url, params=params, timeout=10, verify=False)
    response.raise_for_status()

    if response.status_code == requests.codes.NOT_FOUND:
        logger.info('A user with email {} does NOT exist'
                    .format(smart_str(email)))

        return None

    sso_id = json.loads(response.text).get('sso_id', None)

    logger.info('A user with email {} already exists with SSO ID {}'
                .format(smart_str(email), sso_id))

    return sso_id


def get_remote_user_by_sso_id(sso_id):
    logger.info('Getting remote user with sso_id "{}"'.format(sso_id))

    url = app_settings.REMOTE_USER_URL.format(sso_id=sso_id) + '?with_password=true'
    params = {
        'sso_id': sso_id
    }
    response = requests.get(url=url, params=params, timeout=10, verify=False)
    response.raise_for_status()

    if response.status_code == requests.codes.NOT_FOUND:
        logger.info('A user with sso_id "{}" does NOT exist'.format(smart_str(sso_id)))
        return

    response_data = json.loads(response.text)
    sso_id = response_data.get('sso_id', None)

    if sso_id is None:
        logger.warning('No user with sso_id "{}" found'.format(sso_id))
        return

    logger.info('A user with sso_id "{}" exists'.format(smart_str(sso_id)))
    return response_data


@transaction.atomic
def create_local_user_from_object(user_object, verified=False):
    logger.info('Creating local user from object "{}". Verified: {}'.format(user_object, verified))

    username = user_object.get('username')
    sso_id = user_object.get('sso_id', None)
    sso_rev = user_object.get('sso_rev', 0)

    User = get_user_model()

    if sso_id is not None:
        sso_id = smart_str(sso_id)

        if User.objects.filter(sso_app_profile__sso_id=sso_id).count() > 0:
            raise Exception('Profile with sso_id "{}" already present'.format(sso_id))

        logger.info('Creating local user with sso_id "{}" and sso_rev "{}" ...'.format(sso_id, sso_rev))

    if User.objects.filter(username=username).count() > 0:
        raise Exception('User with username "{}" already present'.format(username))

    new_user = User()

    user_object_profile = user_object.get('profile', None)

    setattr(new_user, '__dssoa__creating', True)
    setattr(new_user, '__dssoa__profile__sso_id', sso_id)
    setattr(new_user, '__dssoa__profile__sso_rev', sso_rev)

    setattr(new_user, '__dssoa__profile__object', user_object_profile)

    # saving model there (commit) implies profile creation with pre-defined attrs sso_id, sso_rev
    new_user = update_user(new_user, user_object, commit=True)

    email = user_object.get('email', None)

    if email is not None:
        if EmailAddress.objects.filter(email__iexact=email).count() > 0:
            raise Exception('EmailAddress already present')

        created_email = EmailAddress.objects.create(user=new_user,
                                                    email=email,
                                                    verified=verified,
                                                    primary=True)
        logger.info(
            'A new EmailAddress for {0} has been created with id {1}'
            ''.format(
                email, created_email.id))

        if verified:
            logger.info(
                '{0} must NOT confirm email {1}'.format(new_user, email))
        else:
            logger.info(
                '{0} must confirm email {1}'.format(new_user, email))

    logger.info('local user created "{}"'.format(new_user))

    setattr(new_user, '__dssoa__creating', False)

    return new_user


@transaction.atomic
def create_local_user_from_apigateway_headers(request):
    consumer_custom_id = request.META.get(app_settings.APIGATEWAY_CONSUMER_CUSTOM_ID_HEADER)
    consumer_groups = request.META.get(app_settings.APIGATEWAY_CONSUMER_GROUPS_HEADER, None)

    logger.info('Creating local user from apigateway consumer username "{}"'.format(smart_str(consumer_custom_id)))

    sso_id = consumer_custom_id
    sso_rev = 0
    username = consumer_custom_id

    user_object = {
        'sso_id': sso_id,
        'sso_rev': sso_rev,
        'username': username
    }

    if consumer_groups is not None:
        user_object['profile'] = {
            'groups': get_apigateway_profile_groups_from_header(consumer_groups)
        }

    new_user = create_local_user_from_object(user_object)

    return new_user


@transaction.atomic
def create_local_user_from_jwt(decoded_jwt):
    logger.info('Creating local user from jwt')

    sso_id = decoded_jwt.get('sso_id')
    sso_rev = decoded_jwt.get('sso_rev')
    username = decoded_jwt.get('username', sso_id)

    user_object = {
        'sso_id': sso_id,
        'sso_rev': sso_rev,
        'username': username
    }

    new_user = create_local_user_from_object(user_object)

    #setattr(new_user, 'sso_app_profile', get_or_create_user_profile(new_user, Profile, profile_object))

    return new_user


@transaction.atomic
def create_local_user_from_remote_backend(remote_user_object, can_subscribe=False):
    # Creates new user only by profile object
    logger.info('Creating local user from remote backend')

    new_user = create_local_user_from_object(remote_user_object,
                                             verified=getattr(remote_user_object, 'email_verified', False))

    setattr(new_user, '__dssoa__remote_user', remote_user_object)  # noqa (subscription required)

    return new_user


@transaction.atomic
def update_local_user_from_remote_backend(user, remote_user_object, commit=True):
    logger.info('Updating local user with sso_id "{}" ...'.format(user.sso_id))

    user = update_user(user, remote_user_object, commit)

    setattr(user, '__dssoa__remote_user', remote_user_object)

    remote_object_profile = remote_user_object['profile']
    # update profile
    setattr(user, 'sso_app_profile', update_profile(user.sso_app_profile, remote_object_profile, commit))

    return user


@transaction.atomic
def replicate_remote_user(sso_id):
    logger.info('Replicating user with sso_id "{}" from remote backend'.format(sso_id))

    remote_user_object = fetch_remote_user(sso_id=sso_id)

    User = get_user_model()
    prev_user = User.objects.filter(sso_app_profile__sso_id=sso_id).first()

    if prev_user is None:
        user = create_local_user_from_remote_backend(remote_user_object)

    else:
        logger.info('User with sso_id "{}" already present, updating'.format(sso_id))
        user = update_local_user_from_remote_backend(prev_user, remote_user_object)

    return user
