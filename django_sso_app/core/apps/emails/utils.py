import logging

logger = logging.getLogger('django_sso_app')


def unconfirm_all_user_emails(user, request=None):
    logger.info('Unconfirming all emails for user "{}"'.format(user))

    return user.emailaddress_set.filter(verified=True).update(verified=False)
