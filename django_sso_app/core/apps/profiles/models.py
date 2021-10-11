import logging
import uuid

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from django_countries.fields import CountryField

from ..groups.models import Group
from ... import app_settings
from ...models import CreatedAtModel, UpdatableModel, DeactivableModel, PublicableModel

logger = logging.getLogger('django_sso_app')


def _get_new_uuid():
    return str(uuid.uuid4())


class SsoIdPKManager(models.Manager):
    use_in_migrations = True

    def get_by_natural_key(self, sso_id):
        return self.get(sso_id=sso_id)


class AbstractProfileModel(CreatedAtModel, UpdatableModel, DeactivableModel, PublicableModel):
    """
    Profile abstract model

    """

    class Meta:
        abstract = True

    objects = SsoIdPKManager()

    def natural_key(self):
        return (self.sso_id, )

    sso_id = models.CharField(_('sso id'), max_length=36, unique=True, default=_get_new_uuid, db_index=True)  # unique on not null , editable=False
    sso_rev = models.PositiveIntegerField(_('sso revision'), default=1)

    django_user_username = models.CharField(_('user username'), max_length=150, null=True, blank=True, editable=False)
    django_user_email = models.EmailField(_('email address'), null=True, blank=True, editable=False)

    external_id = models.CharField(_('external id'), max_length=36, null=True, blank=True, db_index=True)

    ssn = models.CharField(_('social security number'), max_length=255, null=True, blank=True)
    phone = models.CharField(_('phone'), max_length=255, null=True, blank=True)

    first_name = models.CharField(_('first name'), max_length=255, null=True,
                                  blank=True)
    last_name = models.CharField(_('last name'), max_length=255, null=True,
                                 blank=True)
    alias = models.CharField(_('alias'), max_length=255, null=True, blank=True)

    description = models.TextField(_('description'), null=True, blank=True)
    picture = models.TextField(_('picture'), null=True, blank=True)

    birthdate = models.DateField(_('birthdate'), null=True, blank=True)
    country_of_birth = CountryField(_('country of birth'), max_length=46, null=True, blank=True)

    latitude = models.FloatField(_('latitude'), null=True, blank=True)
    longitude = models.FloatField(_('longitude'), null=True, blank=True)

    # country = models.CharField(_('country'), max_length=46, null=True,
    #                            blank=True)
    country = CountryField(_('country'), max_length=46, null=True, blank=True)

    address = models.TextField(_('address'), null=True, blank=True)
    language = models.CharField(_('language'), max_length=3, null=True, blank=True)

    gender = models.CharField(_('gender'), max_length=15, null=True, blank=True)

    company_name = CountryField(_('company name'), max_length=255, null=True, blank=True)

    expiration_date = models.DateTimeField(_('expiration date'), null=True, blank=True)

    completed_at = models.DateTimeField(_('profile completion date'), null=True, blank=True)

    unsubscribed_at = models.DateTimeField(_('unsubscription date'), null=True, blank=True)

    meta = models.TextField(_('meta'), null=True, blank=True)

    created_by_event = models.BooleanField(_('created by event'), default=False)

    @property
    def is_unsubscribed(self):
        return self.unsubscribed_at is not None

    @is_unsubscribed.setter
    def is_unsubscribed(self, value):
        self.unsubscribed_at = timezone.now()


class Profile(AbstractProfileModel):
    class Meta:
        app_label = 'django_sso_app'
        verbose_name = _('Profile')

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                null=True, blank=True,
                                verbose_name=_("user"),
                                related_name="sso_app_profile")

    apigw_consumer_id = models.CharField(_('API gateway consumer id'), max_length=36, null=True, blank=True)

    groups = models.ManyToManyField(Group, blank=True, related_name='sso_app_profiles', verbose_name=_('groups'),
                                    related_query_name='sso_app_profile')

    def __str__(self):
        return '{}:{}:{}'.format(self.email, self.sso_id, self.username)

    def update_rev(self, commit=False):
        if getattr(self, '__rev_updated', False):
            logger.debug('Rev already updated')
        else:
            logger.info(
                'Updating rev for User {}, from {} to {}, commit? {}'.format(self,
                                                                             self.sso_rev,
                                                                             self.sso_rev + 1,
                                                                             commit))

            self.sso_rev = models.F('sso_rev') + 1

            setattr(self, '__rev_updated', True)

        if commit:
            self.save()

    def save(self, *args, **kwargs):
        # pre save
        creating = self._state.adding

        # set profile completed_at if all required fields are set
        if not self.is_incomplete and self.completed_at is None:
            self.completed_at = timezone.now()

        if not creating:
            user = self.user

            if getattr(user, '__dssoa__apigateway_update', False):
                logger.debug('Profile updated by apigateway, skipping rev update')
            elif getattr(user, '__dssoa__creating', False):
                logger.debug('Created, skipping rev update')
            else:
                logger.debug('Profile model updated, updating rev')
                self.update_rev(False)

        super(AbstractProfileModel, self).save(*args, **kwargs)

        # post save
        # refresh instance from db because of rev_update
        if not creating:
            self.refresh_from_db()

    def get_relative_rest_url(self):
        return reverse("django_sso_app_profile:rest-detail", args=[self.sso_id])

    def add_to_group(self, group_name, creating=False):
        logger.info('Adding "{}" to group "{}"'.format(self, group_name))

        g, _created = Group.objects.get_or_create(name=group_name)
        if _created:
            logger.info('New group "{}" created'.format(g))

        if creating:
            setattr(self.user, '__dssoa__creating', True)

        if g not in self.groups.all():
            self.groups.add(g)

        if creating:
            setattr(self.user, '__dssoa__creating', False)

    def remove_from_group(self, group_name, creating=False):
        logger.info('Removing "{}" from group "{}"'.format(self, group_name))

        g, _created = Group.objects.get_or_create(name=group_name)
        if _created:
            logger.info('New group "{}" created'.format(g))

        if creating:
            setattr(self.user, '__dssoa__creating', True)

        if g in self.groups.all():
            self.groups.remove(g)

        if creating:
            setattr(self.user, '__dssoa__creating', False)

    @property
    def username(self):
        if getattr(self, 'user', None) is not None:
            return self.user.username
        else:
            return self.django_user_username

    @property
    def email(self):
        if getattr(self, 'user', None) is not None:
            return self.user.email
        else:
            return self.django_user_email

    @property
    def is_incomplete(self):
        for field in app_settings.REQUIRED_PROFILE_FIELDS:
            if getattr(self, field, None) in (None, ''):
                logger.debug('Empty "{}" field'.format(field))
                return True

        return False

    @property
    def must_subscribe(self):
        if app_settings.SERVICE_SUBSCRIPTION_REQUIRED:
            user_service_subscription = self.subscriptions.filter(service__service_url=app_settings.SERVICE_URL).first()

            if user_service_subscription is None or user_service_subscription.is_unsubscribed:
                return True

        return self.is_unsubscribed


"""
class DjangoSsoAppUserStatus(object):
    def __init__(self, is_active, is_unsubscribed, is_to_subscribe):
        self.is_active = is_active
        self.is_unsubscribed = is_unsubscribed
        self.is_to_subscribe = is_to_subscribe

    def __repr__(self):
        return ("{}(is_active={}, is_unsubscribed={}, is_to_subscribe={})"
                .format(self.__class__.__name__, self.is_active,
                        self.is_unsubscribed, self.is_to_subscribe))

    @staticmethod
    def get_user_status(is_unsubscribed, subscriptions, email_verified=True):
        _is_active = app_settings.DEACTIVATE_USER_ON_UNSUBSCRIPTION

        if is_unsubscribed:  # is unsubscribed from sso
            return DjangoSsoAppUserStatus(is_active=_is_active,
                                          is_unsubscribed=True,
                                          is_to_subscribe=False)
        else:  # is still subscribed to sso
            for subscription in subscriptions:
                if subscription["service_url"] == app_settings.APP_URL:  #
                    # subscription found
                    if subscription["is_unsubscribed"]:  # user is unsubscribed from service
                        return DjangoSsoAppUserStatus(is_active=(_is_active
                                                                 and email_verified),
                                                      is_unsubscribed=True,
                                                      is_to_subscribe=False)
                    return DjangoSsoAppUserStatus(is_active=email_verified,
                                                  is_unsubscribed=False,
                                                  is_to_subscribe=False)

            # is NOT subscribed
            return DjangoSsoAppUserStatus(
                is_active=email_verified, is_unsubscribed=False,
                is_to_subscribe=app_settings.SERVICE_SUBSCRIPTION_IS_MANDATORY)

"""
