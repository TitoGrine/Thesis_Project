import math
import time
import gensim.downloader as downloader

from pprint import pprint
from decouple import config
from elasticsearch import Elasticsearch
from pyspark import SparkContext, SparkConf

from src.utils import chunks, WORD_MODEL, ES_INDEX, ES_ENDPOINT, get_searching_config, get_discovery_config, \
    get_extraction_config
from src.searching import get_initial_users, test_query_results
from src.discovery import get_words_embedding, batch_request_profiles, analyze_profile
from src.extraction import process_profile_links

conf = SparkConf().setAppName("Test").setMaster("local[*]")
spark_context = SparkContext(conf=conf)


# TODO:


class color:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def connect_elasticsearch():
    _es = Elasticsearch(ES_ENDPOINT, http_auth=('elastic', config('ES_ELASTIC_PASSWORD')), verify_certs=False)

    return _es if _es.ping() else None


def pipeline():
    # ElasticSearch
    _es = connect_elasticsearch()

    if _es is None:
        print("Failed to connect to elasticsearch")
        return

    _es.indices.delete(index=ES_INDEX, ignore=[400, 404])

    # Configurations
    searching_config = get_searching_config()
    keywords, tweets_per_user = get_discovery_config()
    extraction_params = get_extraction_config()

    # Searching
    ids = get_initial_users(searching_config)

    print(f"{color.OKCYAN}Gathered {len(ids)} initial profiles.{color.ENDC}")

    # Discovery
    word_model = downloader.load(WORD_MODEL)
    embedded_keywords = get_words_embedding(keywords, word_model)

    word_model_bv = spark_context.broadcast(word_model)

    id_chunks = list(chunks(ids, 100))

    rdd = spark_context.parallelize(id_chunks)

    profile_responses = rdd.flatMap(batch_request_profiles)

    analyzed_profiles = profile_responses.map(
        lambda pf: analyze_profile(pf, embedded_keywords, tweets_per_user, word_model_bv.value))

    related_profiles = analyzed_profiles.filter(lambda profile: profile is not None)

    # Extraction
    final_profiles = related_profiles.map(lambda profile: process_profile_links(profile, extraction_params)).collect()

    for final_profile in final_profiles:
        try:
            _es.index(index=ES_INDEX, id=final_profile.get('id'), document=final_profile)
        except Exception as e:
            print(f"{color.FAIL}Error posting to index: {e}{color.ENDC}")


def main():
    start_time = time.time()

    pipeline()

    end_time = time.time()

    print("Total run time: {:02d}:{:02d}".format(math.floor((end_time - start_time) / 60),
                                                 round((end_time - start_time) % 60)))


if __name__ == '__main__':
    main()
    # test()
