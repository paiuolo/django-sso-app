import logging
import requests

from django.contrib.auth import get_user_model
from django.db import transaction

from .... import app_settings

logger = logging.getLogger('django_sso_app')
User = get_user_model()


def create_apigw_consumer(custom_id):
    logger.info('creating apigw consumer with custom_id {}'.format(custom_id))

    url = app_settings.APIGATEWAY_HOST + "/consumers/"
    data = {'custom_id': custom_id}

    r = requests.post(url, json=data)

    status_code = r.status_code
    try:
        response_body = r.json()
    except:
        logger.debug('Response ({}) has no payload'.format(status_code))
        response_body = None

    logger.debug('apigw response ({0}) {1}'.format(status_code, response_body))

    return status_code, response_body


def get_apigw_consumer(consumer_id, custom_id=None):
    if custom_id is None:
        logger.info('getting apigw consumer {}'.format(consumer_id))
        url = app_settings.APIGATEWAY_HOST + "/consumers/{}".format(consumer_id)
    else:
        logger.info('getting apigw consumer with custom_id {}'.format(custom_id))
        url = app_settings.APIGATEWAY_HOST + "/consumers/?custom_id={}".format(custom_id)

    r = requests.get(url)

    status_code = r.status_code
    try:
        response_body = r.json()
    except:
        logger.debug('Response ({}) has no payload'.format(status_code))
        response_body = None

    logger.debug('apigw response ({0}) {1}'.format(status_code, response_body))

    if custom_id is None:
        return status_code, response_body
    else:
        if status_code == 200:
            if len(response_body['data']):
                return status_code, response_body['data'][0]
            else:
                return 404, None
        else:
            return status_code, response_body


def delete_apigw_consumer(consumer_id):
    logger.info('deleting apigw consumer for {}'.format(consumer_id))

    url = app_settings.APIGATEWAY_HOST + "/consumers/" + consumer_id

    r = requests.delete(url)

    status_code = r.status_code
    try:
        response_body = r.json()
    except:
        logger.info('Response ({}) has no payload'.format(status_code))
        response_body = None

    logger.debug('apigw response ({0}) {1}'.format(status_code, response_body))
    return status_code, response_body


def create_apigw_consumer_jwt(consumer_id):
    logger.info('creating apigw consumer jwt for {}'.format(consumer_id))

    url = app_settings.APIGATEWAY_HOST + "/consumers/" + consumer_id + "/jwt/"
    data = {}

    r = requests.post(url, json=data)

    status_code = r.status_code
    try:
        response_body = r.json()
    except:
        logger.debug('Response ({}) has no payload'.format(status_code))
        response_body = None

    logger.debug('apigw response ({0}) {1}'.format(status_code, response_body))
    return status_code, response_body


def delete_apigw_consumer_jwt(consumer_id, jwt_id):
    logger.info('deleting apigw consumer jwt {} for {}'.format(jwt_id, consumer_id))

    url = '{}/{}/{}/jwt/{}'.format(app_settings.APIGATEWAY_HOST, "consumers", consumer_id, jwt_id)

    logger.info('calling kong url "{}"'.format(url))

    r = requests.delete(url)

    status_code = r.status_code

    logger.info('apigw response ({0}) {1}'.format(status_code, None))
    return r.status_code, None


def get_apigw_consumer_jwts(consumer_id):
    logger.info('getting apigw consumer jwts for {}'.format(consumer_id))

    url = app_settings.APIGATEWAY_HOST + "/consumers/" + consumer_id + "/jwt/"

    r = requests.get(url)

    status_code = r.status_code
    try:
        response_body = r.json()
    except:
        logger.info('Response ({}) has no payload'.format(status_code))
        response_body = None

    logger.info('apigw response ({0}) {1}'.format(status_code, response_body))
    return status_code, response_body


def create_apigw_consumer_acl(consumer_id, group_name):
    logger.info('creating apigw consumer acl {} for {}'.format(group_name,
                                                               consumer_id))

    url = app_settings.APIGATEWAY_HOST + "/consumers/" + consumer_id + "/acls/"
    data = {"group": group_name}

    r = requests.post(url, json=data)

    status_code = r.status_code
    try:
        response_body = r.json()
    except:
        logger.info('Response ({}) has no payload'.format(status_code))
        response_body = None

    logger.info('apigw response ({0}) {1}'.format(status_code, response_body))
    return status_code, response_body


def get_apigw_consumer_acls(consumer_id):
    logger.info('getting apigw consumer groups for {}'.format(consumer_id))

    url = app_settings.APIGATEWAY_HOST + "/consumers/" + consumer_id + "/acls/"

    r = requests.get(url)

    status_code = r.status_code
    try:
        response_body = r.json()
    except:
        logger.info('Response ({}) has no payload'.format(status_code))
        response_body = None

    logger.info('apigw response ({0}) {1}'.format(status_code, response_body))
    return status_code, response_body


def delete_apigw_consumer_acl(consumer_id, group_name):
    logger.info('deleting apigw consumer acl {} for {}'.format(group_name,
                                                               consumer_id))

    url = app_settings.APIGATEWAY_HOST + "/consumers/" + consumer_id + "/acls/" + group_name

    r = requests.delete(url)

    status_code = r.status_code

    logger.info('apigw response ({0}) {1}'.format(status_code, None))
    return r.status_code, None


def add_apigw_consumer_to_groups_acls(consumer_id, group_names):
    # adding apigw consumer to profile groups
    """
    profile_groups = app_settings.DEFAULT_PROFILE_GROUPS + \
                     list(profile.groups.values_list('name', flat=True))
    """

    for group_name in group_names:
        status_code, acl = create_apigw_consumer_acl(consumer_id, group_name)
        if status_code not in (201, 409):  # 409 when already created
            logger.error(
                'Error ({0}) creating apigw consumer acl, {1}'.format(
                    status_code, acl))
            raise Exception(
                "Error {0} creating apigw consumer acl, {1}".format(
                    status_code, acl))


# profile

@transaction.atomic
def get_or_create_profile_apigw_consumer(profile, force_recreate=False):
    logger.info('getting or creating apigw consumer for "{}"'.format(profile))
    consumer_id = profile.apigw_consumer_id

    if consumer_id is None:
        status_code, consumer = get_apigw_consumer(consumer_id, profile.sso_id)
        update_consumer_id = True
    else:
        status_code, consumer = get_apigw_consumer(consumer_id)
        update_consumer_id = False

    if status_code == 200:
        if force_recreate:
            if update_consumer_id:
                consumer_id = consumer['id']

            # deleting old consumer
            _status_code, _res = delete_apigw_consumer(consumer_id)
            # creating new consumer
            _status_code, consumer = create_apigw_consumer(profile.sso_id)

            if status_code == 201:

                # disable sso_rev update
                setattr(profile.user, '__dssoa__apigateway_update', True)
                # setting apigw_consumer_id
                profile.apigw_consumer_id = consumer['id']
                # save profile
                profile.save()
                setattr(profile.user, '__dssoa__apigateway_update', False)

                return consumer
            else:
                logger.error('Error ({0}) creating consumer for "{1}'.format(status_code, profile))
                raise Exception('Error ({0}) creating consumer for "{1}"'.format(status_code, profile))

        else:
            if update_consumer_id:
                # disable sso_rev update
                setattr(profile.user, '__dssoa__apigateway_update', True)
                # setting apigw_consumer_id
                profile.apigw_consumer_id = consumer['id']
                # save profile
                profile.save()
                setattr(profile.user, '__dssoa__apigateway_update', False)

            return consumer

    elif status_code == 404:
        # consumer not found
        status_code, consumer = create_apigw_consumer(profile.sso_id)

        if status_code == 201:
            # disable sso_rev update
            setattr(profile.user, '__dssoa__apigateway_update', True)
            # setting apigw_consumer_id
            profile.apigw_consumer_id = consumer['id']
            # save profile
            profile.save()
            # add consumer to profile groups
            add_apigw_consumer_to_groups_acls(consumer['id'],
                                              app_settings.DEFAULT_PROFILE_GROUPS +
                                              list(profile.groups.values_list('name', flat=True)))
            setattr(profile.user, '__dssoa__apigateway_update', False)

            return consumer

        elif status_code == 409:
            _status_code, consumer = get_apigw_consumer(consumer_id, profile.sso_id)

            setattr(profile.user, '__dssoa__apigateway_update', True)
            # setting apigw_consumer_id
            profile.apigw_consumer_id = consumer['id']
            # save profile
            profile.save()
            # add consumer to profile groups
            add_apigw_consumer_to_groups_acls(consumer['id'],
                                              app_settings.DEFAULT_PROFILE_GROUPS +
                                              list(profile.groups.values_list('name', flat=True)))
            setattr(profile.user, '__dssoa__apigateway_update', False)

            return consumer

        else:
            logger.error('Error ({0}) creating consumer for "{1}'.format(status_code, profile))
            raise Exception('Error ({0}) creating consumer for "{1}"'.format(status_code, profile))

    else:
        logger.error('Error ({0}) getting consumer for "{1}: {1}'.format(status_code, profile))
        raise Exception('Error ({0}) getting consumer for "{1}"'.format(status_code, profile))


def get_profile_apigw_consumer_id(profile, force_recreate=False):
    return get_or_create_profile_apigw_consumer(profile, force_recreate)['id']
