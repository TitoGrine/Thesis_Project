import os
import shutil
from pprint import pprint

from searching import get_initial_users, test_query_results
from discovery import identify_related_profiles
from extraction import process_profiles


# TODO: Check links_visited variable. Make it global? See how it affect other uses of the module.


def test():
    test_tweets = test_query_results()

    pprint(test_tweets)


def main():
    if os.path.exists("output"):
        shutil.rmtree("output", True)
        os.mkdir("output")

    ids = get_initial_users()
    related_profiles = identify_related_profiles(ids)
    process_profiles(related_profiles)


if __name__ == '__main__':
    main()
    # test()
