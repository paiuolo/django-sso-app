# Boostable functions
#
# import pyximport
# pyximport.install()

import random
import hashlib
from string import ascii_uppercase, digits
from urllib.parse import urlparse


def get_random_string(n: int) -> str:
    """
    Returns n characters random string
    :param n:
    :return:  str
    """
    return ''.join(random.choice(ascii_uppercase + digits) for _ in range(n))


def get_url_host(url: str) -> str:
    """
    Returns given url host base path
    :param url:
    :return: str
    """
    parsed_url = urlparse(url)

    if parsed_url.scheme is not None and parsed_url.hostname is not None:
        return_url = parsed_url.scheme + '://' + parsed_url.hostname

        if parsed_url.port is not None:
            return_url += ':' + str(parsed_url.port)

        return return_url


def lists_differs(a: list, b: list) -> bool:
    """
    Checks if a and b differs
    :param a:
    :param b:
    :return:
    """
    a.sort()
    b.sort()

    return a != b


def get_numeric_hash(s: str,
                     HASH_LENGTH: int = 2,
                     ENCODING: str = 'utf-8') -> str:
    """
    Returns HASH_LENGTH string hash [0-1]*
    :param s:
    :param HASH_LENGTH:
    :param ENCODING:
    :return:
    """
    num = str(int(hashlib.sha256(s.encode(ENCODING)).hexdigest(), 16) % 10**HASH_LENGTH)

    if len(num) == 1:
        num = '0' + num

    return num
