import logging

from django.contrib.messages import get_messages
from django.utils.encoding import force_str

logger = logging.getLogger('django_sso_app')


def get_request_messages_string(request):
    """
    Serializes django messages

    :param request:
    :return:
    """
    storage = get_messages(request)
    _messages = []
    for message in storage:
        _messages.append(force_str(message))

    return ', '.join(_messages)
