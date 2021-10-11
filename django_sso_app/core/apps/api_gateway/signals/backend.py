import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import m2m_changed
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver

from ....permissions import is_django_staff
from ...devices.models import Device
from ...groups.models import Group
from ...profiles.models import Profile
from ..utils import delete_apigw_consumer, create_apigw_consumer_jwt, delete_apigw_consumer_jwt, \
                    create_apigw_consumer_acl, delete_apigw_consumer_acl, get_profile_apigw_consumer_id

logger = logging.getLogger('django_sso_app')

User = get_user_model()


# device

@receiver(pre_save, sender=Device)
def create_device_apigw_jwt(sender, instance, **kwargs):
    device = instance
    profile = device.profile
    user = profile.user
    creating = instance._state.adding

    if creating and not is_django_staff(user):
        logger.info('Creating apigw JWT for Device "{}"'.format(device))

        apigateway_consumer_id = get_profile_apigw_consumer_id(profile)
        status_code, response = create_apigw_consumer_jwt(apigateway_consumer_id)

        if status_code != 201:
            # delete_apigw_consumer(username)
            logger.error(
                'Error ({}) creating apigw consumer JWT, "{}"'.format(
                    status_code, response))
            raise Exception(
                'Error ({}) creating apigw consumer jwt'.format(status_code))

        device.apigw_jwt_id = response.get('id')
        device.apigw_jwt_key = response.get('key')
        device.apigw_jwt_secret = response.get('secret')


@receiver(pre_delete, sender=Device)
def delete_device_api_jwt(sender, instance, **kwargs):
    device = instance
    logger.info('Deleting apigw JWT for Device "{}", jwt_id: "{}"'.format(device, device.apigw_jwt_id))

    apigateway_consumer_id = get_profile_apigw_consumer_id(device.profile)
    status_code, response = delete_apigw_consumer_jwt(apigateway_consumer_id, device.apigw_jwt_id)

    logger.debug('Kong JWT deleted ({0}), {1}'.format(status_code, response))
    if status_code >= 300:
        if status_code != 404:
            # delete_apigw_consumer(username)
            logger.error('Error ({}) Deleting apigw JWT for Device "{}", "{}"'.format(status_code, device, response))

            raise Exception(
                "Error deleting apigw consumer jwt, {}".format(status_code))


# profile

@receiver(pre_delete, sender=Profile)
def delete_apigw_profile_consumer(sender, instance, **kwargs):
    profile = instance
    user = profile.user

    if not is_django_staff(user):
        logger.info('Profile "{}" will be deleted, removing api gateway consumer'.format(profile))

        apigateway_consumer_id = get_profile_apigw_consumer_id(profile)
        status_code, response = delete_apigw_consumer(apigateway_consumer_id)
        logger.debug('Api gateway consumer deletion: ({0}), {1}'.format(status_code, response))

        if status_code >= 300:
            if status_code != 404:
                # delete_apigw_consumer(username)
                logger.error(
                    'Error ({0}) Deleting apigw consumer for User {1}, {2}'.format(
                        status_code, profile, response))
                raise Exception(
                    "Error deleting apigw consumer, {}".format(status_code))


# group

@receiver(m2m_changed, sender=Profile.groups.through)
def api_gateway_signal_handler_when_profile_is_added_to_or_removed_from_group(action, instance, pk_set, **kwargs):

    profile = instance
    user = profile.user

    if not is_django_staff(user):
        is_loaddata = getattr(user, '__dssoa__loaddata', False)
        #is_apigateway_update = getattr(user, '__dssoa__apigateway_update', False)

        apigateway_consumer_id = get_profile_apigw_consumer_id(profile)
        logger.debug('apigateway_consumer_id on m2m_changed "{}"'.format(apigateway_consumer_id))

        if action == 'pre_add':

            for pk in pk_set:
                group = Group.objects.get(id=pk)

                logger.info('creating api gateway acl group "{}" for profile "{}"'.format(group.name, profile))

                apigateway_consumer_id = get_profile_apigw_consumer_id(profile)
                status_code, resp = create_apigw_consumer_acl(apigateway_consumer_id, group.name)

                if status_code < 400:
                    logger.debug('api gateway acl group created {}, {}'.format(status_code, resp))

                    if not is_loaddata:  # or is_apigateway_update):
                        if group.name != 'incomplete':
                            profile.update_rev(True)

                elif status_code == 409:
                    logger.debug('acl group "{} already created'.format(group.name))

                else:
                    logger.exception('error ({}) creating api gateway acl group'.format(status_code))

        elif action == 'pre_remove':
            for pk in pk_set:
                group = Group.objects.get(id=pk)
                logger.info('deleting apigw acl group "{}" for "{}"'.format(group, profile))

                apigateway_consumer_id = get_profile_apigw_consumer_id(profile)
                status_code, resp = delete_apigw_consumer_acl(apigateway_consumer_id, group.name)

                if status_code < 400:
                    logger.debug('"{}" DELETED, updating profile sso_rev'.format(group))

                    if not is_loaddata:
                        if group.name != 'incomplete':
                            profile.update_rev(True)

                elif status_code == 404:
                    logger.debug('acl group "{} already deleted'.format(group.name))

                else:
                    logger.exception('error ({}) deleting api gateway acl group'.format(status_code))
