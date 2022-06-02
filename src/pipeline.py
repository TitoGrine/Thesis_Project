import time

from datetime import datetime
from pprint import pprint

from pyspark import SparkContext
from gensim import downloader as downloader

from src import ES_INDEX_CONFIG, get_searching_config, get_discovery_config, get_extraction_config, \
    get_initial_users, WORD_MODEL, get_words_embedding, chunks, batch_request_profiles, analyze_profile, \
    process_profile_links, connect_elasticsearch, save_search_result, ES_INDEX_SEARCH, profile_index_mapping


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


def setup_elasticsearch(search_id: str, config: dict, state: str):
    config['state'] = state

    _es = connect_elasticsearch()

    _es.index(index=f"{ES_INDEX_CONFIG}", id=search_id, document=config)

    _es.indices.create(index=f"{ES_INDEX_SEARCH}_{search_id}", body=profile_index_mapping)

    _es.close()


def save_search_state(search_id: str, config: dict, state: str):
    config['state'] = state

    _es = connect_elasticsearch()

    _es.index(index=f"{ES_INDEX_CONFIG}", id=search_id, document=config)

    _es.close()


def pipeline(spark_context: SparkContext, config: dict, search_id):
    config['timestamp'] = datetime.now()

    setup_elasticsearch(search_id=search_id, config=config, state="running")

    start_time = time.time()

    try:
        # Configurations
        searching_config = get_searching_config(config)
        keywords, tweets_per_user = get_discovery_config(config)
        links_per_user, entities_params = get_extraction_config(config)

        # Searching
        ids = get_initial_users(searching_config)

        # Discovery
        word_model = downloader.load(WORD_MODEL)
        embedded_keywords = get_words_embedding(keywords, word_model)

        word_model_bv = spark_context.broadcast(word_model)

        id_chunks = list(chunks(ids, 100))

        rdd = spark_context.parallelize(id_chunks)

        profile_responses = rdd.flatMap(batch_request_profiles)

        related_profiles = profile_responses.map(
            lambda pf: analyze_profile(pf, embedded_keywords, tweets_per_user, word_model_bv.value)).filter(
            lambda profile: profile is not None)

        # Extraction
        final_profiles = related_profiles.map(
            lambda profile: process_profile_links(profile, links_per_user, entities_params))

        # ElasticSearch
        results = final_profiles.map(lambda profile: save_search_result(search_id, profile)).filter(
            lambda res: res is not None).collect()

        print(f"Gathered {len(results)} profiles")

        config['duration'] = time.time() - start_time

        save_search_state(search_id=search_id, config=config, state="completed")

    except Exception as error:
        config['duration'] = time.time() - start_time
        config['error'] = str(error)

        save_search_state(search_id=search_id, config=config, state="error")
