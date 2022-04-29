import os
import json
from pprint import pprint

import tweepy

from decouple import config
from bloom_filter2 import BloomFilter

api = tweepy.Client(bearer_token=config('TWITTER_BEARER_TOKEN'))

search_words = ["sex", "onlyfans", "camgirl", "escort"]
exclude_words = ["pornhub"]
hashtags = ["onlyfans", "loyalfans", "caming", "escort"]
ISO_allowed_countries = ['US', 'CA']
languages_allowed = ['en']

# Maximum allowed is 500
MAX_RESULTS = 10


def build_query():
    keywords = " OR ".join(search_words)
    excluded = " AND ".join([f"-{token}" for token in exclude_words])
    include_hashtags = " OR ".join([f"#{hashtag}" for hashtag in hashtags])
    countries = " OR ".join([f"place_country:{ISO_code}" for ISO_code in ISO_allowed_countries])
    languages = " OR ".join([f"lang:{lang}" for lang in languages_allowed])

    query = f"(({keywords}) OR ({include_hashtags})) ({excluded}) ({countries}) ({languages}) -is:retweet -is:nullcast"

    print(query)

    return query


def sample_tweets(query):
    res = api.search_all_tweets(query, sort_order="relevancy", max_results=MAX_RESULTS)

    pprint(res)


def main():
    query = build_query()
    sample_tweets(query)


if __name__ == '__main__':
    main()
