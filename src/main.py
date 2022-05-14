import math
import os
import shutil
import time
from pprint import pprint

import numpy

from searching import get_initial_users, test_query_results
from discovery import identify_related_profiles
from extraction import process_profiles


# TODO: Check if all profiles are being crawled. I don't think so but I don't know why


def test():
    test_tweets = test_query_results()

    pprint(test_tweets)


def main():
    if os.path.exists("output"):
        shutil.rmtree("output", True)

    os.mkdir("output")

    ids = get_initial_users()

    start_time = time.time()

    related_profiles = identify_related_profiles(ids)

    end_time = time.time()
    print(
        "Elapsed time: {:02d}:{:02d}".format(math.floor((end_time - start_time) / 60),
                                             round((end_time - start_time) % 60)))

    print(f"Identified {len(related_profiles)} potentially related users.")
    # process_profiles(related_profiles)


if __name__ == '__main__':
    main()
    # test()
