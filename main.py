import os
import math
import time
import shutil
import gensim.downloader as downloader

from pprint import pprint
from pyspark import SparkContext, SparkConf

from src.utils import chunks, WORD_MODEL, get_searching_config, get_discovery_config, get_extraction_config
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


def test():
    test_tweets = test_query_results()

    pprint(test_tweets)


def pipeline():
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
    related_profiles.map(lambda profile: process_profile_links(profile, extraction_params)).collect()


def main():
    if os.path.exists("output"):
        shutil.rmtree("output", True)

    os.mkdir("output")

    start_time = time.time()

    pipeline()

    end_time = time.time()

    print(
        "Total run time: {:02d}:{:02d}".format(math.floor((end_time - start_time) / 60),
                                               round((end_time - start_time) % 60)))


if __name__ == '__main__':
    main()
    # test()
