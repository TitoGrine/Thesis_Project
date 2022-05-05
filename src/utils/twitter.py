import re

from gensim.parsing import preprocessing, strip_multiple_whitespaces

from . import normalize_unicode_text, remove_urls, remove_mentions, remove_retweet_tag, remove_sanitized_chars


def valid_tweet(tweet) -> bool:
    return 'lang' not in tweet or tweet.get('lang') == "en"


def get_retweet_id(tweet) -> int or None:
    referenced_tweets = tweet.get('referenced_tweets', [])

    for referenced_tweet in referenced_tweets:
        if referenced_tweet.get('type') == 'retweeted':
            # TODO: Check if it is necessary to convert to int
            return int(referenced_tweet['id'])

    return None


def process_twitter_text(text):
    text = normalize_unicode_text(text)

    return preprocessing.preprocess_string(text, filters=[
        remove_urls, remove_sanitized_chars, remove_retweet_tag, remove_mentions, str.lower,
        normalize_unicode_text, preprocessing.strip_tags, preprocessing.strip_punctuation, preprocessing.strip_numeric,
        preprocessing.strip_non_alphanum, preprocessing.strip_multiple_whitespaces, preprocessing.remove_stopwords,
        preprocessing.strip_short])


def process_twitter_name(name) -> str:
    name = normalize_unicode_text(name)

    name = re.sub(r"\(.*\)", "", name)
    name = re.sub(r"([#@])\w*\b", "", name)
    name = re.sub(r"\|", "", name)

    return strip_multiple_whitespaces(name).strip()
