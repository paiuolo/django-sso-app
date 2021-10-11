import requests

from time import sleep
from jinja2 import Template


def get_es_query(template, **kwargs):
    return Template(template).render(**kwargs)


def call_backend(uri, es_query, jwt=None, apikey=None):
    """
    Send POST request to elasticsearch.
    """

    headers = {
        'Content-Type': 'application/json'
    }

    if jwt is not None:
        headers['Authorization'] = 'Bearer {}'.format(jwt)
    elif apikey is not None:
        headers['apikey'] = '{}'.format(apikey)

    try:
        resp = requests.post(uri, headers=headers, data=str(es_query))
        resp.raise_for_status()

    except Exception as e:
        # When status code is 502 elasticsearch is reindexing. Should retry.
        if e.response.status_code == 502:
            sleep(5)
            return call_backend(uri, es_query, jwt=jwt, apikey=apikey)
        else:
            raise

    else:
        return resp.json()
