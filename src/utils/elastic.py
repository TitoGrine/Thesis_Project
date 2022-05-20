from decouple import config
from elasticsearch import Elasticsearch

from .constants import ES_ENDPOINT


def connect_elasticsearch():
    _es = Elasticsearch(ES_ENDPOINT, http_auth=('elastic', config('ES_ELASTIC_PASSWORD')), verify_certs=False)

    return _es if _es.ping() else None
