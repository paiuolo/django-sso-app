import logging

from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from ....permissions import is_django_staff
from ...profiles.models import Profile
from ..models import Group
from ..utils import set_default_user_groups, set_default_profile_groups

logger = logging.getLogger('django_sso_app')
User = get_user_model()


@receiver(m2m_changed, sender=Profile.groups.through)
def signal_handler_when_user_profile_is_added_or_removed_from_group(action, instance, reverse, model, pk_set, using, **kwargs):
    """
    Update sso_rev when user enter/exit groups
    """

    profile = instance
    user = profile.user

    is_loaddata = getattr(user, '__dssoa__loaddata', False)
    is_creating = getattr(user, '__dssoa__creating', False)
    #is_apigateway_update = getattr(user, '__dssoa__apigateway_update', False)
    is_updating_groups = getattr(user, '__dssoa__updating_default_groups', False)

    must_update_rev = (not is_loaddata) and \
                      (not is_creating) and \
                      (not is_updating_groups) and \
                      (not is_django_staff(user))
    #                       (not is_apigateway_update) and \
    groups_updated = False

    if action == 'pre_add':
        groups_updated = True
        for pk in pk_set:
            group = Group.objects.get(id=pk)
            logger.info('Profile "{}" entered group "{}"'.format(profile, group))

    elif action == 'pre_remove':
        groups_updated = True
        for pk in pk_set:
            group = Group.objects.get(id=pk)
            logger.info('Profile "{}" exited from group "{}"'.format(profile, group))

    # updating rev

    if groups_updated and must_update_rev:
        profile.update_rev(True)


@receiver(post_save, sender=Profile)
def update_groups_on_user_profile_updated(sender, instance, created, **kwargs):
    """
    Profile model has been updated, check user profile completeness and default groups
    """
    if kwargs['raw']:
        # https://github.com/django/django/commit/18a2fb19074ce6789639b62710c279a711dabf97
        return

    profile = instance
    user = profile.user

    if created and not is_django_staff(user):
        # default groups
        set_default_profile_groups(profile)

        # check profile groups
        user_object_profile = getattr(profile.user, '__dssoa__profile__object', None)

        if user_object_profile is not None:
            group_names = user_object_profile.get('groups', [])
        else:
            group_names = []

        for gn in group_names:
            profile.add_to_group(gn, creating=True)


@receiver(post_save, sender=User)
def add_user_model_to_default_groups_on_creation(sender, instance, created, **kwargs):
    """
    User model has been updated
    """
    user = instance

    if kwargs['raw']:
        # https://github.com/django/django/commit/18a2fb19074ce6789639b62710c279a711dabf97
        return

    if created and not is_django_staff(user):
        set_default_user_groups(user)

