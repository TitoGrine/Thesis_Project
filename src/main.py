import os
import shutil
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
    print(f"Collected {len(ids)} users.")
    related_profiles = identify_related_profiles(ids)
    print(f"Identified {len(related_profiles)} potentially related users.")
    process_profiles(related_profiles)


if __name__ == '__main__':
    main()
    # test()
