import logging

# import pyximport
# pyximport.install()

from django.db import transaction

from ...permissions import is_django_staff
from ...functions import lists_differs
from ... import app_settings
from ..services.models import Service
from .models import Profile as Profile

logger = logging.getLogger('django_sso_app')


@transaction.atomic
def create_update_profile_subscriptions(profile, update_object):
    """
    Update local profile subscriptions
    """
    logger.info('Updating profile subscriptions for "{}"'.format(profile))

    remote_subscriptions = update_object.get('subscriptions', None)

    if remote_subscriptions is not None and len(remote_subscriptions) > 0:
        logger.debug('remote_profile_subscriptions "{}"'.format(remote_subscriptions))

        if app_settings.APP_ENABLED:  # disable rev update for app shapes
            setattr(profile.user, '__dssoa__creating', True)

        active_subscriptions = []
        disabled_subscriptions = []
        for s in remote_subscriptions:
            if s['is_unsubscribed']:
                disabled_subscriptions.append(s['service_url'])
            else:
                active_subscriptions.append(s['service_url'])

        active_services = []
        disabled_services = []
        for url in active_subscriptions:
            service, created = Service.objects.get_or_create(service_url=url)
            active_services.append(service)

        for url in disabled_subscriptions:
            service, created = Service.objects.get_or_create(service_url=url)
            disabled_services.append(service)

        """
        active_services = Service.objects.filter(service_url__in=active_subscriptions,
                                                 is_active=True)
        disabled_services = Service.objects.filter(service_url__in=disabled_subscriptions,
                                                   is_active=True)
        """

        active_subscriptions = []
        disabled_subscriptions = []
        for s in active_services:
            subscription, updated = s.subscribe(profile)
            if updated:
                logger.info('Subscription updated "{}"'.format(subscription))
                active_subscriptions.append(subscription)

        for s in disabled_services:
            subscription, updated = s.unsubscribe(profile)
            if updated:
                logger.info('Subscription updated "{}"'.format(subscription))
                disabled_subscriptions.append(subscription)

        if app_settings.APP_ENABLED:  # restore rev update for app shapes
            setattr(profile.user, '__dssoa__creating', False)

        # return
        return active_subscriptions, disabled_subscriptions

    return None, None


@transaction.atomic
def update_profile_groups(profile, update_object):
    logger.debug('update_profile_groups')

    actual_groups_list = update_object.get('groups', None)

    if actual_groups_list is not None:
        if app_settings.APP_ENABLED:  # disable rev update for app shapes
            setattr(profile.user, '__dssoa__creating', True)

        active_groups = []
        disabled_groups = []

        previous_groups_list = list(profile.groups.order_by('name').values_list('name', flat=True))

        if lists_differs(previous_groups_list, actual_groups_list):
            logger.info('Must update profile groups for "{}"'.format(profile))
            logger.info('From {} to {}'.format(previous_groups_list, actual_groups_list))

            # try to remove profile from removed groups
            for group_name in previous_groups_list:
                if group_name not in actual_groups_list:
                    profile.remove_from_group(group_name)
                    disabled_groups.append(group_name)

            # try to add profile to new groups
            for group_name in actual_groups_list:
                if group_name not in previous_groups_list:
                    profile.add_to_group(group_name)
                    active_groups.append(group_name)

        if app_settings.APP_ENABLED:  # disable rev update for app shapes
            setattr(profile.user, '__dssoa__creating', True)

        return active_groups, disabled_groups

    return None, None


@transaction.atomic
def update_profile(profile, update_object, commit=True):
    logger.info('Updating profile fields for "{}"'.format(profile))

    for f in app_settings.PROFILE_FIELDS + ('sso_rev', 'meta'):
        if hasattr(profile, f):
            new_val = update_object.get(f, None)
            if new_val is not None:
                setattr(profile, f, new_val)
                logger.debug('profile field updated "{}":"{}"'.format(f, new_val if f != 'password' else '*'))

    if commit:
        profile.save()

    if profile.pk:  # if profile model is in DB
        logger.debug('Try update profile groups and subscriptions')
        # update groups
        _active_groups, _disabled_groups = update_profile_groups(profile, update_object)
        # update subscriptions
        _active_subscriptions, _disabled_subscriptions = create_update_profile_subscriptions(profile, update_object)

    return profile


def get_or_create_user_profile(user, initials=None, commit=True):
    logger.debug('get or create user profile')

    try:
        profile = user.sso_app_profile

    except Profile.DoesNotExist:
        logger.info('User "{}" has no profile, creating one'.format(user))

        setattr(user, '__dssoa__creating', True)

        profile = Profile(user=user, django_user_email=user.email, django_user_username=user.username)

        sso_id = getattr(user, '__dssoa__profile__sso_id', None)
        if sso_id is not None:
            sso_rev = getattr(user, '__dssoa__profile__sso_rev', 0)
            profile.sso_id = sso_id
            profile.sso_rev = sso_rev
        else:
            # django staff users sso_id equals username
            if is_django_staff(user):
                profile.sso_id = user.username
                profile.sso_rev = 0

        profile_initials = initials or getattr(user, '__dssoa__profile__object', None)

        if profile_initials is not None:
            logger.debug('Got profile initials "{}"'.format(profile_initials))
            profile = update_profile(profile, profile_initials, commit=commit)
        else:
            logger.debug('No profile initials')
            if commit:
                profile.save()

        setattr(user, '__dssoa__creating', False)

    # force user sso_app_profile object field
    #setattr(user, 'sso_app_profile', profile)

    return profile
