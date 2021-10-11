import json

from datetime import timezone

from celery import shared_task
from celery.utils.log import get_task_logger

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import translation
from django.conf import settings
# http://ask.github.io/celery/cookbook/tasks.html#ensuring-a-task-is-only-executed-one-at-a-time
from django.core.cache import cache

from allauth.account.models import EmailAddress

from ..profiles.models import Profile
from ..groups.models import Group
from ..users.utils import create_local_user_from_object
from .models import RequestForCredentialsEventListener
from .utils import fetch_event_type_events, sort_event_type_events

User = get_user_model()
MODULE_NAME = 'events'
LOCK_EXPIRE = 60 * 5 # Lock expires in 5 minutes


# https://stackoverflow.com/questions/12414821/checking-a-nested-dictionary-using-a-dot-notation-string-a-b-c-d-e-automatica
def _put(d, keys, item):
    if "." in keys:
        key, rest = keys.split(".", 1)
        if key not in d:
            d[key] = {}
        _put(d[key], rest, item)
    else:
        d[keys] = item


def _get(d, keys):
    if "." in keys:
        key, rest = keys.split(".", 1)
        return _get(d[key], rest)
    else:
        return d.get(keys, None)


def _create_users_by_events(logger):
    """
    Check user related events
    :param logger:
    :return:
    """
    users_created = 0

    instantiated_event_listeners = RequestForCredentialsEventListener.objects.filter(is_active=True)

    for event_listener in instantiated_event_listeners:
        last_profile = Profile.objects.filter(created_by_event=True).order_by('-created_at').first()
        from_date = last_profile.created_at if last_profile else event_listener.created_at
        from_timestamp = from_date.timestamp()
        event_type = event_listener.event_type
        confirm_email = event_listener.confirm_email
        default_password = event_listener.default_password

        logger.info('Getting "{}" events from date "{}"'.format(event_type, from_date))
        rfc_events, _count = fetch_event_type_events(event_type, from_timestamp)

        for event in sort_event_type_events(rfc_events, event_type):
            try:
                with transaction.atomic():
                    logger.debug('Last "{}" event: "{}"'.format(event_type, event))

                    # set email
                    user_email = event.get(event_listener.email_field, None)
                    if user_email is None:
                        raise Exception('Event object has no "{}" field'.format(event_listener.email_field))

                    # set username
                    user_username = event.get(event_listener.email_field, user_email)

                    profile_object = {}
                    for field in RequestForCredentialsEventListener.profile_fields:
                        field_key = getattr(event_listener, '{}_field'.format(field), None)
                        if field_key is not None:
                            # val = event.get(field_key, None)
                            val = _get(event, field_key)
                            logger.debug('Event profile field {}:{}'.format(field_key, val))
                            if val is not None:
                                profile_object[field] = val

                    # create user
                    new_user = create_local_user_from_object({
                        'email': user_email,
                        'username': user_username,
                        'profile': profile_object
                    }, verified=confirm_email)

                    # set created by event
                    new_user.sso_app_profile.created_by_event = True
                    new_user.sso_app_profile.meta = json.dumps({
                        'event': event
                    })
                    new_user.sso_app_profile.save()

                    # set profile groups
                    profile_group_field_key = getattr(event_listener, 'group_field', None)
                    if profile_group_field_key is not None:
                        profile_group_name = event.get(profile_group_field_key, None)
                        if profile_group_name is not None:
                            new_user.sso_app_profile.add_to_group(profile_group_name, creating=True)

                    # set user password
                    if default_password is not None:
                        logger.info('Setting default password')
                        new_user.set_password(default_password)
                        new_user.save()

                    # send confirmation email
                    if not confirm_email:
                        logger.info('Sending confirmation email to"{}"'.format(user_email))
                        language_code = new_user.sso_app_profile.language or settings.LANGUAGE_CODE
                        translation.activate(language_code)
                        EmailAddress.objects.get(email=user_email).send_confirmation()

                    logger.info('New user: "{}"'.format(new_user))
                    users_created += 1

            except Exception as e:
                logger.exception('Error: {}. Can not create user by event: {}'.format(e, event))

    return users_created


@shared_task(bind=True)
def create_users_by_events(self, **kwargs):
    _name = 'create_users_by_events'
    name = '{}.{}'.format(MODULE_NAME, _name)
    _logger = get_task_logger(name)

    # The cache key consists of the module and task names
    lock_id = '{}-lock'.format(name)

    # cache.add fails if if the key already exists
    acquire_lock = lambda: cache.add(lock_id, "true", LOCK_EXPIRE)
    # memcache delete is very slow, but we have to use it to take
    # advantage of using add() for atomic locking
    release_lock = lambda: cache.delete(lock_id)

    if acquire_lock():
        try:
            ret = _create_users_by_events(_logger)
        finally:
            release_lock()
        return ret

    _logger.debug("{} is already being executed by another worker".format(name))
