import math
import os
import shutil
import time
from pprint import pprint
from decouple import config
from elasticsearch import Elasticsearch

from searching import get_initial_users, test_query_results
from discovery import identify_related_profiles
from extraction import process_profiles

from src.utils import ES_INDEX


# TODO:


def connect_elasticsearch():
    _es = Elasticsearch("https://localhost:9200", http_auth=('elastic', config('ES_ELASTIC_PASSWORD')),
                        verify_certs=False)

    return _es if _es.ping() else None


def test():
    # test_tweets = test_query_results()

    # pprint(test_tweets)

    _es = connect_elasticsearch()

    if _es is None:
        print("Failed to connect to elasticsearch")
        return

    try:
        _es.index(index="test", document={
            'name': 'Testing',
            'value': 20
        })
    except Exception as e:
        print(f"Error posting to index: {e}")


def main():
    if os.path.exists("output"):
        shutil.rmtree("output", True)

    os.mkdir("output")

    _es = connect_elasticsearch()

    if _es is None:
        print("Failed to connect to elasticsearch")
        return

    ids = get_initial_users()

    start_time = time.time()

    related_profiles = identify_related_profiles(ids)

    end_time = time.time()
    print(
        "Time for profile discovery: {:02d}:{:02d}".format(math.floor((end_time - start_time) / 60),
                                                           round((end_time - start_time) % 60)))

    print(f"Identified {len(related_profiles)} potentially related users.")

    start_time = time.time()

    final_profiles = process_profiles(related_profiles)

    end_time = time.time()
    print(
        "Time for link extraction: {:02d}:{:02d}".format(math.floor((end_time - start_time) / 60),
                                                         round((end_time - start_time) % 60)))

    for profile in final_profiles:
        try:
            _es.index(index=ES_INDEX, document=profile)
        except Exception as e:
            print(f"Error posting to index: {e}")


if __name__ == '__main__':
    main()
    # test()
