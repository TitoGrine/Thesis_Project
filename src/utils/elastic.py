from decouple import config
from elasticsearch import Elasticsearch

from .constants import ES_ENDPOINT, ES_INDEX_SEARCH


def connect_elasticsearch():
    _es = Elasticsearch(ES_ENDPOINT, basic_auth=('elastic', config('ES_ELASTIC_PASSWORD')), verify_certs=False,
                        ssl_show_warn=False, timeout=30, max_retries=3)

    return _es if _es.ping() else None


def save_search_result(search_id, profile_info):
    _es = connect_elasticsearch()

    if _es is None:
        print(f"Error connecting to elasticsearch.")
        return None

    try:
        profile_id = profile_info.get('id')
        _es.index(index=f"{ES_INDEX_SEARCH}_{search_id}", id=profile_id, document=profile_info)

        _es.close()
        return profile_id
    except Exception as e:
        print(f"Error posting to index: {e}")
        return None
