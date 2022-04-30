import os
import math
import json
from pprint import pprint

import tweepy

from time import sleep
from decouple import config
from bloom_filter2 import BloomFilter

from utils import process_twitter_name, process_twitter_text

api = tweepy.Client(bearer_token=config('TWITTER_BEARER_TOKEN'))

search_words = ["onlyfans", "camgirl", "escort"]
exclude_words = ["pornhub", "gay"]
search_hashtags = ["onlyfans", "loyalfans", "caming", "escort", "adultwork"]
ISO_allowed_countries = ['US', 'CA']
languages_allowed = ['en']

NUM_USERS = 10

USER_FIELDS = ["id", "username", "name"]


def build_query():
    keywords = " OR ".join(search_words)
    excluded = " ".join([f"-{token}" for token in exclude_words])
    hashtags = " OR ".join([f"#{hashtag}" for hashtag in search_hashtags])
    countries = " OR ".join([f"place_country:{ISO_code}" for ISO_code in ISO_allowed_countries])
    languages = " OR ".join([f"lang:{lang}" for lang in languages_allowed])

    query = f"(({keywords}) OR ({hashtags})) ({excluded}) ({countries}) ({languages}) -is:retweet -is:reply -is:nullcast"

    return query


def extract_users(tweets, users, user_set):
    tweets_info = []

    for tweet, user in zip(tweets, users):
        user_set.add((user['id'], user['username']))

        tweets_info.append({
            "user_id": user['id'],
            "username": user['username'],
            "name": process_twitter_name(user['name']),
            "text": process_twitter_text(tweet['text'])
        })

    return tweets_info


def sample_tweets(query):
    next_token = None

    max_results = min(NUM_USERS, 500)
    max_calls = round(math.ceil(NUM_USERS / max_results) * 1.5)
    users = set()
    call_count = 0

    tweets_info = []

    while len(users) < NUM_USERS and call_count < max_calls:
        try:
            res = api.search_all_tweets(query, user_fields=USER_FIELDS, expansions="author_id", sort_order="recency",
                                        max_results=max_results, next_token=next_token, end_time="2022-04-20T00:00:00Z")
        except tweepy.errors.TooManyRequests:
            sleep(1)
            continue
        except Exception as e:
            print(f"Unexpected error while searching tweets: {e}")
            break

        call_count += 1

        if res.meta['result_count'] == 0:
            break

        tweets_info.extend(extract_users(res.data, res.includes['users'], users))

        if 'next_token' not in res.meta:
            print(call_count)
            break

        next_token = res.meta['next_token']

    with open("test/test.json", "w") as f:
        json.dump({"tweets": tweets_info}, f)

    with open("test/test.txt", "w") as f:
        for id, username in users:
            f.write(f"{id} : {username}\n")


def main():
    query = build_query()
    sample_tweets(query)


if __name__ == '__main__':
    main()
