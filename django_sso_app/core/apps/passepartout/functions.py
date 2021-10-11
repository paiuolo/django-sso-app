# Boostable functions
#
# import pyximport
# pyximport.install()

from typing import Optional


def get_referer(APP_DOMAIN: str,
                 DJANGO_SSO_APP_BACKEND_DOMAINS_DICT: dict,
                 DJANGO_SSO_APP_BACKEND_DOMAINS: list,
                 DJANGO_SSO_APP_BACKEND_FULL_URLS_CHAIN: list) -> Optional[str]:
    """
    Extracts referer from request header
    :param referer:
    :param APP_DOMAIN
    :param DJANGO_SSO_APP_BACKEND_DOMAINS_DICT:
    :param DJANGO_SSO_APP_BACKEND_DOMAINS:
    :param DJANGO_SSO_APP_BACKEND_FULL_URLS_CHAIN:
    :return:
    """

    _index_previous_should_be = DJANGO_SSO_APP_BACKEND_DOMAINS_DICT[APP_DOMAIN] - 1
    if _index_previous_should_be < 0:
        _last_sso_instance = DJANGO_SSO_APP_BACKEND_DOMAINS[-1]
        if _last_sso_instance == APP_DOMAIN:
            referer = None
        else:
            referer = DJANGO_SSO_APP_BACKEND_FULL_URLS_CHAIN[-1]
            # Referrer was empty, setting as LAST SSO instance
    else:
        referer = DJANGO_SSO_APP_BACKEND_FULL_URLS_CHAIN[_index_previous_should_be]
        # Referrer was empty, setting as PREVIOUS SSO instance

    return referer


def get_next_bump(actual: str,
                  DJANGO_SSO_APP_BACKEND_FULL_URLS_CHAIN: list) -> Optional[str]:
    """
    Returns next django-sso-app backend instance
    :param actual:
    :param DJANGO_SSO_APP_BACKEND_FULL_URLS_CHAIN:
    :return:
    """
    if actual in DJANGO_SSO_APP_BACKEND_FULL_URLS_CHAIN:
        pos = DJANGO_SSO_APP_BACKEND_FULL_URLS_CHAIN.index(actual)

    last_pos = len(DJANGO_SSO_APP_BACKEND_FULL_URLS_CHAIN) - 1

    if pos < last_pos:
        next_pos = DJANGO_SSO_APP_BACKEND_FULL_URLS_CHAIN[pos + 1]
    else:
        next_pos = DJANGO_SSO_APP_BACKEND_FULL_URLS_CHAIN[0]

    if next_pos == actual:
        return None

    return next_pos
