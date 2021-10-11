import logging

import requests

from ... import app_settings

logger = logging.getLogger('django_sso_app')


def subscribe_to_backend_service(sso_id, encoded_jwt=None):
    """
    Creates a new profile subscription

    :param sso_id:
    :return:
    """
    logger.info("Subscribing profile with SSO ID {sso_id} to service"
                " {service_name} ..."
                .format(sso_id=sso_id,
                        service_name=app_settings.SERVICE_URL))
    if encoded_jwt is None:
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Token {}".format(app_settings.BACKEND_STAFF_TOKEN)
        }
    else:
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(encoded_jwt)
        }

    # Get all available services
    url = app_settings.BACKEND_SERVICES_URL

    response = requests.get(url=url, headers=headers, timeout=10, verify=False)
    response.raise_for_status()

    sso_services = response.json()

    # Find out the id for current service
    service_id = None
    for sso_service in sso_services:
        if sso_service["service_url"] == app_settings.APP_URL:
            service_id = sso_service['id']
            break
    if not service_id:
        _msg = ("Current service {} is not listed in SSO!"
                .format(app_settings.APP_URL))
        raise Exception(_msg)

    # Subscribe to current service
    url = (app_settings.USER_SUBSCRIPTIONS_CREATE_URL.format(sso_id=sso_id, service_id=service_id))

    response = requests.post(url=url, headers=headers, timeout=10, verify=False)
    response.raise_for_status()

    logger.info("Profile with SSO ID {sso_id} was successfully subscribed to"
                " service {service_name}!"
                .format(sso_id=sso_id,
                        service_name=app_settings.APP_URL))
