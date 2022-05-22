import os
import time

import tweepy
from decouple import config

from .extract import extract_profile_info
from .classify import calculate_profile_score
from src.utils import TOPIC_SIMILARITY_THRESHOLD, USER_FIELDS, OUTPUT_DIR, PROFILE_INFO_FILE, print_elapsed_time

if "json" in PROFILE_INFO_FILE:
    import json as serializer
else:
    import pickle as serializer

api = tweepy.Client(bearer_token=config('TWITTER_BEARER_TOKEN'))


def save_profile(profile_info):
    # TODO: Perhaps change to id in the future
    profile_dir = f"{OUTPUT_DIR}/{profile_info['username']}"

    if not os.path.exists(profile_dir):
        os.mkdir(profile_dir)

    file_mode = "x" if ".json" in PROFILE_INFO_FILE else "xb"

    with open(f"{profile_dir}/{PROFILE_INFO_FILE}", file_mode) as f:
        serializer.dump(profile_info, f)


def analyze_profile(response, keywords, tweets_per_user, word_model):
    profile_info = extract_profile_info(response, tweets_per_user)

    if profile_info is None:
        return None

    description = profile_info.get('description')
    tweets = profile_info.pop('tweets')
    retweets = profile_info.pop('retweets')

    score = calculate_profile_score(keywords, word_model, description, tweets, retweets)

    if score > TOPIC_SIMILARITY_THRESHOLD and len(profile_info.get('links', [])) > 0:
        profile_info['score'] = "{:.3f}".format(score)

        return profile_info

    return None


def batch_request_profiles(ids):
    responses = api.get_users(ids=ids, user_fields=USER_FIELDS).data

    return [response.data for response in responses]
