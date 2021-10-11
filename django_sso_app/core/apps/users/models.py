import logging

from django.urls import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.hashers import get_hasher, identify_hasher

from ... import app_settings
from ..groups.models import Group

logger = logging.getLogger('django_sso_app')


class DjangoSsoAppUserModelMixin(object):
    # username = models.CharField(_('username'), max_length=150, unique=True)  # django
    email = models.EmailField(_('email address'), blank=True)  # django

    """
    @property
    def previous_serialized_as_string(self):
        return getattr(self, '__serialized_as_string')

    @property
    def serialized_as_string(self):
        serialized = ''
        for f in app_settings.USER_FIELDS + ('password', 'is_active'):
            serialized += '__' + str(getattr(self, f, None))

        logger.debug('serialized_as_string {}'.format(serialized))
        return serialized
    """

    @property
    def password_has_been_updated(self):
        return getattr(self, '__dssoa__old_password', None) != self.password

    @property
    def email_has_been_updated(self):
        return getattr(self, '__dssoa__old_email', None) != self.email or \
               getattr(self, '__dssoa__email_updated', False)

    @property
    def sso_app_new_email(self):
        if self.email_has_been_updated:
            return self.email

    @property
    def username_has_been_updated(self):
        return getattr(self, '__dssoa__old_username', None) != self.username or \
               getattr(self, '__dssoa__username_updated', False)

    @property
    def sso_app_new_username(self):
        if self.username_has_been_updated:
            return self.username

    @property
    def password_has_been_hardened(self):
        has_password = getattr(self, '__dssoa__old_password', self.password) not in (None, '')

        try:
            if has_password:
                old_hashed_password = getattr(self, '__dssoa__old_password')
                old_hasher = identify_hasher(old_hashed_password)
                new_hashed_password = self.password
                new_hasher = identify_hasher(new_hashed_password)

                try:
                    hasher = get_hasher('default')
                    return hasher.must_update(old_hashed_password)

                except AssertionError:
                    logger.exception('Error checking password hardened')
                    return old_hasher != new_hasher
            else:
                return False

        except Exception:
            logger.exception('Exception on checking password hardened')
            return False

    def __init__(self, *args, **kwargs):
        super(DjangoSsoAppUserModelMixin, self).__init__(*args, **kwargs)
        if app_settings.BACKEND_ENABLED:
            setattr(self, '__dssoa__old_password', self.password)
            setattr(self, '__dssoa__old_email', self.email)
            setattr(self, '__dssoa__old_username', self.username)
            # setattr(self, '__serialized_as_string', self.serialized_as_string)  # replaced by '..__user_loggin_in'

    def save(self, *args, **kwargs):
        # pre save
        super(DjangoSsoAppUserModelMixin, self).save(*args, **kwargs)
        # post save
        #setattr(new_user, 'sso_app_profile', get_or_create_user_profile(new_user, commit=True))

    def get_relative_rest_url(self):
        profile = self.get_sso_app_profile()
        if profile is not None:
            return reverse("django_sso_app_user:rest-detail", kwargs={"sso_id": profile.sso_id})

    def get_sso_app_profile(self):
        return getattr(self, 'sso_app_profile', None)

    @property
    def sso_id(self):
        profile = self.get_sso_app_profile()
        if profile is not None:
            return profile.sso_id

        return None

    @property
    def sso_rev(self):
        profile = self.get_sso_app_profile()
        if profile is not None:
            return profile.sso_rev

        return 0

    @property
    def must_subscribe(self):
        profile = self.get_sso_app_profile()
        if profile is not None:
            return profile.must_subscribe

        return not self.is_active

    @property
    def is_subscribed(self):
        profile = self.get_sso_app_profile()
        if profile is not None:
            return profile.is_subscribed

        return self.is_active

    def add_to_group(self, group_name, creating=False):
        logger.info('Adding "{}" to group "{}"'.format(self, group_name))

        g, _created = Group.objects.get_or_create(name=group_name)
        if _created:
            logger.info('New group "{}" created'.format(g))

        if creating:
            setattr(self, '__dssoa__creating', True)

        if g not in self.groups.all():
            self.groups.add(g)

        if creating:
            setattr(self, '__dssoa__creating', False)

    def remove_from_group(self, group_name, creating=False):
        logger.info('Removing "{}" from group "{}"'.format(self, group_name))

        g, _created = Group.objects.get_or_create(name=group_name)
        if _created:
            logger.info('New group "{}" created'.format(g))

        if creating:
            setattr(self, '__dssoa__creating', True)

        if g in self.groups.all():
            self.groups.remove(g)

        if creating:
            setattr(self, '__dssoa__creating', False)
