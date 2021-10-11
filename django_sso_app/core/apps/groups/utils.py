import logging

# import pyximport
# pyximport.install()

from django.db import transaction

from ...functions import lists_differs
from ... import app_settings

logger = logging.getLogger('django_sso_app')


@transaction.atomic
def set_default_user_groups(user):
    """
    Update User model groups.
    Checks for DJANGO_SSO_APP_DEFAULT_USER_GROUPS +
    """
    logger.debug('set_default_user_groups')

    setattr(user, '__dssoa__updating_default_groups', True)

    previous_groups_list = list(user.groups.order_by('name').values_list('name', flat=True))
    actual_groups_list = list(set(previous_groups_list + app_settings.DEFAULT_USER_GROUPS))

    if lists_differs(previous_groups_list, actual_groups_list):
        logger.info('Must update default user groups for "{}"'.format(user))
        logger.info('From {} to {}'.format(previous_groups_list, actual_groups_list))

        # try to add user to new groups
        for group_name in actual_groups_list:
            if group_name not in previous_groups_list:
                user.add_to_group(group_name)

        # try to remove user from removed groups
        for group_name in previous_groups_list:
            if group_name not in actual_groups_list:
                user.remove_from_group(group_name)

    setattr(user, '__dssoa__updating_default_groups', False)


@transaction.atomic
def set_default_profile_groups(profile):
    logger.debug('set_default_profile_groups')

    setattr(profile.user, '__dssoa__updating_default_groups', True)

    previous_groups_list = list(profile.groups.order_by('name').values_list('name', flat=True))
    actual_groups_list = list(set(previous_groups_list +
                                  app_settings.DEFAULT_PROFILE_GROUPS))

    if profile.is_incomplete:
        if 'incomplete' not in actual_groups_list:
            logger.debug('Adding to incomplete group')
            actual_groups_list.append('incomplete')
    else:
        if 'incomplete' in actual_groups_list:
            logger.debug('Removing from incomplete group')
            actual_groups_list.remove('incomplete')

    if lists_differs(previous_groups_list, actual_groups_list):
        logger.info('Must set default profile groups for "{}"'.format(profile))
        logger.info('From {} to {}'.format(previous_groups_list, actual_groups_list))

        # try to add profile to new groups
        for group_name in actual_groups_list:
            if group_name not in previous_groups_list:
                profile.add_to_group(group_name)

        # try to remove profile from removed groups
        for group_name in previous_groups_list:
            if group_name not in actual_groups_list:
                profile.remove_from_group(group_name)

    setattr(profile.user, '__dssoa__updating_default_groups', False)
