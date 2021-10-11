import logging

from .... import app_settings
from . import elastic

logger = logging.getLogger('django_sso_app')
ELASTICSEARCH_INDEX_URL = app_settings.EVENTS_HOST + '/{}/_search'.format(app_settings.EVENTS_INDEX)


def fetch_event_type_events(event_type: str, from_date: str, jwt: str = None, apikey: str = None) -> (object, int):
    """
    Returns event objects given event_type

    :param event_type:
    :param from_date:
    :param jwt:
    :param apikey:
    :return:
    """
    ES_QUERY = """{
      "from": 0,
      "size": 1000,
      "sort" : [
        { "doc.timestamp" : {"order" : "asc"}}
      ],
      "query": {
        "bool": {
          "filter": [
             {
              "range": {
                "doc.timestamp": {
                  "gte": "{{ from_date }}"
                }
              }
            },
            {
              "terms": {
                "doc.type": [
                  "{{ event_type }}"
                ]
              }
            }
          ]
        }
      }
    }"""

    def _fetch_data(event_type, from_date):
        es_url = ELASTICSEARCH_INDEX_URL
        es_query = elastic.get_es_query(ES_QUERY,
                                        event_type=event_type,
                                        from_date=from_date)
        # print('CALLING ES', es_query, es_url)
        return elastic.call_backend(es_url, es_query, jwt=jwt, apikey=apikey)

    def _cleaned_data(data):
        for d in data:
            yield d['_source']['doc']

    es_response = _fetch_data(event_type, from_date)

    instance_tasks, count = es_response['hits']['hits'], es_response['hits']['total']['value']

    # return generator and total hits count
    return _cleaned_data(instance_tasks), count


def sort_event_type_events(events, event_type):
    # filter related procedure events, sort ascending by timestamp and return
    return sorted(filter(lambda x: x['type'] == event_type, events),
                  key=lambda x: x['timestamp'], reverse=False)
