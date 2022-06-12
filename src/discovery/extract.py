import tweepy
import validators

from time import sleep
from decouple import config
from tweepy.errors import TooManyRequests
from urllib.parse import urlparse
from src.utils import valid_tweet, get_retweet_id, process_twitter_text, standardize_url, remove_url_query, \
    REFUSE_DOMAINS, TWEET_FIELDS
from bloom_filter2 import BloomFilter

api = tweepy.Client(bearer_token=config('TWITTER_BEARER_TOKEN'))


def add_url_to_links(url, links, links_bf):
    expanded_url = standardize_url(url.get('expanded_url', ""))

    if not validators.url(expanded_url):
        return

    expanded_url_hostname = urlparse(expanded_url).hostname

    stripped_url = remove_url_query(expanded_url)

    if bool([domain for domain in REFUSE_DOMAINS if expanded_url_hostname in domain]) or stripped_url in links_bf:
        return

    links.append(expanded_url)
    links_bf.add(stripped_url)


def extract_profile_base_urls(links, links_bf, profile_entities):
    if profile_entities is None:
        return []

    profile_urls = []

    explicit_urls = profile_entities.get('url', {}).get('urls', [])
    profile_urls.extend(explicit_urls)

    description_urls = profile_entities.get('description', {}).get('urls', [])
    profile_urls.extend(description_urls)

    for url in profile_urls:
        add_url_to_links(url, links, links_bf)


def extract_tweet_urls(tweet):
    return tweet.get('entities', {}).get('urls', [])


def extract_tweet_entities(tweet):
    context_annotations = tweet.get('context_annotations')

    if context_annotations is None:
        return []

    entities = []

    for annotation in context_annotations:
        entity = annotation.get('entity', {}).get('name')

        if entity is not None:
            entities.append(entity)

    return entities


def parse_tweet(tweet, retweets_map) -> dict or None:
    if not valid_tweet(tweet):
        return

    retweet_id = get_retweet_id(tweet)
    is_retweet = bool(retweet_id)

    text = " ".join(process_twitter_text(tweet.get('text') if not is_retweet else retweets_map.get(retweet_id)))
    urls = extract_tweet_urls(tweet) if not is_retweet else []
    entities = extract_tweet_entities(tweet) if not is_retweet else []

    return {
        'is_retweet': is_retweet,
        'urls': urls,
        'entities': entities,
        'text': text,
    }


def extract_tweets_info(response, links, links_bf, entities, tweets, retweets):
    data = response.data
    retweets_map = {
        retweet.id: retweet.text for retweet in response.includes.get('tweets', [])
    }

    if data is None:
        return "", ""

    for tweet in data:
        tweet_info = parse_tweet(tweet.data, retweets_map)

        if tweet_info is None:
            continue

        is_retweet = tweet_info.get('is_retweet', False)
        text = tweet_info.get('text', "")

        if len(text) > 0:
            if not is_retweet:
                tweets.append(text)
            else:
                retweets.append(text)

        for url in tweet_info.get('urls', []):
            add_url_to_links(url, links, links_bf)

        for entity in tweet_info.get('entities', []):
            entities.add(entity)


def extract_profile_tweets_info(profile_info, profile_entities, tweets_per_profile):
    user_id = profile_info['id']

    links = []
    links_bf = BloomFilter()
    entities = set()
    tweets = []
    retweets = []

    extract_profile_base_urls(links, links_bf, profile_entities)

    tweet_count = 0
    next_token = None

    while tweet_count < tweets_per_profile:
        try:
            response = api.get_users_tweets(id=user_id, tweet_fields=TWEET_FIELDS, expansions="referenced_tweets.id",
                                            max_results=100, pagination_token=next_token)
        except TooManyRequests:
            sleep(1)
            continue

        extract_tweets_info(response, links, links_bf, entities, tweets, retweets)

        tweet_count += response.meta['result_count']
        next_token = response.meta.get('next_token')

        if next_token is None:
            break

    profile_info['links'] = links
    profile_info['entities'] = list(entities)
    profile_info['tweets'] = tweets
    profile_info['retweets'] = retweets


def extract_profile_info(response, tweets_per_profile) -> dict or None:
    if response.get('id') is None or response.get('username') is None:
        return

    profile_info = {
        'id': response.get('id'),
        'username': response.get('username'),
        'name': response.get('name'),
        'profile_image': response.get('profile_image_url'),
        'location': response.get('location'),
        'description': response.get('description')
    }

    extract_profile_tweets_info(profile_info, response.get('entities'), tweets_per_profile)

    return profile_info
