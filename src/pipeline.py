import uuid

from datetime import datetime
from gensim import downloader as downloader

from src import ES_INDEX_CONFIG, ES_INDEX_SEARCH, get_searching_config, get_discovery_config, get_extraction_config, \
    get_initial_users, WORD_MODEL, get_words_embedding, chunks, batch_request_profiles, analyze_profile, \
    process_profile_links, connect_elasticsearch


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


def client_message(event, message, search_key=None):
    data = {
        "message": message,
    }

    if search_key: data['key'] = search_key

    return {
        "event": event,
        "data": data
    }


async def pipeline(spark_context, config, request=None):
    if request is not None and await request.is_disconnected():
        return

    yield client_message("update", "Application started.")

    # Configurations
    searching_config = get_searching_config(config)
    keywords, tweets_per_user = get_discovery_config(config)
    extraction_params = get_extraction_config(config)

    config['timestamp'] = datetime.now()

    # Searching
    ids = get_initial_users(searching_config)

    if request is not None and await request.is_disconnected():
        return

    yield client_message("update", f"Collected {len(ids)} initial profiles.")

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
    final_profiles = related_profiles.map(lambda profile: process_profile_links(profile, extraction_params)).collect()

    # ElasticSearch
    _es = connect_elasticsearch()

    if _es is None:
        client_message("error", "Failed to connect to elasticsearch.")
        return

    _es.indices.delete(index="profile", ignore=[400, 404])

    search_id = uuid.uuid4()

    _es.index(index=f"{ES_INDEX_CONFIG}", id=search_id, document=config)

    for final_profile in final_profiles:
        try:
            _es.index(index=f"{ES_INDEX_SEARCH}_{search_id}", id=final_profile.get('id'), document=final_profile)
        except Exception as e:
            print(f"{color.FAIL}Error posting to index: {e}{color.ENDC}")

    if request is not None and await request.is_disconnected():
        return

    yield client_message("end", "Finished search.", search_id)
