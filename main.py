import os
import math
import time
import shutil
from pprint import pprint

from src.searching import get_initial_users, test_query_results
from src.discovery import identify_related_profiles
from src.extraction import process_profiles
from pyspark import SparkContext, SparkConf

conf = SparkConf().setAppName("Test").setMaster("local[*]")
sc = SparkContext(conf=conf)


# TODO:


def test():
    test_tweets = test_query_results()

    pprint(test_tweets)


def main():
    if os.path.exists("output"):
        shutil.rmtree("output", True)
        os.mkdir("output")

    ids = get_initial_users()
    print(f"Collected {len(ids)} users.")

    start_time = time.time()

    related_profiles = identify_related_profiles(ids, sc)

    end_time = time.time()
    print(
        "Elapsed time: {:2}:{:2}".format(math.floor((end_time - start_time) / 60), round((end_time - start_time) % 60)))

    print(f"Identified {len(related_profiles)} potentially related users.")
    # process_profiles(related_profiles)


if __name__ == '__main__':
    main()
    # test()
