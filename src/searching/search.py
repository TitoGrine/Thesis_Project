import math
import tweepy

from time import sleep
from decouple import config
from tweepy.errors import TooManyRequests

from src.utils import get_configuration_section

api = tweepy.Client(bearer_token=config('TWITTER_BEARER_TOKEN'))


def get_searching_config() -> tuple:
    """Gets the configuration parameters from the searching section

    Returns
    -------
    tuple
        All configuration parameters or their default in tuple form

    """
    searching_config = get_configuration_section("searching")

    if "users" not in searching_config:
        raise KeyError("Necessary parameter <users> in searching section is not defined in configuration file.")

    users = searching_config["users"]

    if "keywords" not in searching_config and "hashtags" not in searching_config:
        raise KeyError(
            "Necessary parameters <keywords> and <hashtags> in searching section are not defined in configuration "
            "file. At least one must be defined.")

    keywords = searching_config.get("keywords") or []
    hashtags = searching_config.get("hashtags") or []
    exclude = searching_config.get("_exclude_") or []
    countries = searching_config.get("_countries_") or []
    languages = searching_config.get("_languages_") or ["en"]
    start_time = searching_config.get("_start_time_") or None
    end_time = searching_config.get("_end_time_") or None

    return users, keywords, hashtags, exclude, countries, languages, start_time, end_time


def build_query(keywords, hashtags, exclude, countries, languages) -> str:
    """Builds a Twitter API compliant query for searching tweets

    Parameters
    ----------
    keywords  : list(str)
        Keywords to search for in tweets
    hashtags  : list(str)
        Hashtags to search for in tweets
    exclude   : list(str)
        Words are not accepted in tweets
    countries : list(str)
        ISO codes of countries to accept
    languages : list(str)
        BCP-47 identifiers of languages to accept

    Returns
    -------
    str
        Twitter API compliant query
    """
    keywords = " OR ".join([f"\"{keyword}\"" for keyword in keywords])
    hashtags = " OR ".join([f"#{hashtag}" for hashtag in hashtags])
    exclude = " ".join([f"-\"{token}\"" for token in exclude])
    countries = " OR ".join([f"place_country:{ISO_code}" for ISO_code in countries])
    languages = " OR ".join([f"lang:{lang}" for lang in languages])

    return f"(({keywords}) OR ({hashtags})) ({exclude}) ({countries}) ({languages}) -is:retweet -is:reply -is:nullcast"


def extract_ids(res, ids):
    """Adds the Twitter user IDs from the Response res to the ids set if the user has enough tweets

    Parameters
    ----------
    res : dict
        Twitter Response in json format
    ids : set[str]
        Set of extracted ids
    """
    users = res.includes.get('users') or []

    for user in users:
        public_metrics = user.get('public_metrics', [])

        if public_metrics.get('tweet_count', 0) > 500:
            ids.add(user['id'])


def search_tweets(num_users, query, start_time=None, end_time=None) -> set[str]:
    """Uses the Twitter API: GET /2/tweets/search/all endpoint to collect IDs of potentially relevant users based on their tweets

    Parameters
    ----------
    num_users : int
        The target number of user IDs to collect
    query : str
        Twitter API compliant query to use to search for tweets
    start_time : str, optional
    end_time : str, optional

    Returns
    -------
    set[str]
        Twitter users' IDs

    """
    max_results = min(num_users, 500)
    max_calls = round(math.ceil(num_users / max_results) * 1.5)

    ids = set()
    call_count = 0
    next_token = None

    while len(ids) < num_users and call_count < max_calls:
        try:
            res = api.search_all_tweets(query, expansions="author_id", user_fields=["id", "public_metrics"],
                                        sort_order="recency", start_time=start_time, end_time=end_time,
                                        max_results=max_results, next_token=next_token)
        except TooManyRequests:
            sleep(1)
            continue

        call_count += 1

        if res.meta.get("result_count") == 0:
            break

        extract_ids(res, ids)

        if 'next_token' not in res.meta:
            break

        next_token = res.meta['next_token']

    return ids


def get_initial_users() -> list[str]:
    """Uses the Twitter API and the configurations present in the searching section of the config file to return a
    set of user IDs from potentially relevant profiles

    Returns
    -------
    list[str]
        Twitter users' IDs
    """
    users, keywords, hashtags, exclude, countries, languages, start_time, end_time = get_searching_config()

    query = build_query(keywords, hashtags, exclude, countries, languages)

    ids = search_tweets(users, query, start_time, end_time)

    return list(ids)[:users]


def extract_info(res, results):
    tweets = res.data
    users = res.includes.get('users', [])

    for tweet, user in zip(tweets, users):
        results.append({
            'id': user.get('id', "Error: no ID in user object"),
            'username': user.get('username', "Error: no username in user object"),
            'name': user.get('name', "Error: no name in user object"),
            'tweet': tweet.get('text', "Error: no text in tweet object")
        })


def test_search_tweets(query, start_time=None, end_time=None) -> list[dict]:
    results = []
    call_count = 0
    next_token = None

    while len(results) < 10 and call_count < 2:
        try:
            res = api.search_all_tweets(query, expansions="author_id", user_fields=["id", "username", "name", "url"],
                                        sort_order="recency", start_time=start_time, end_time=end_time, max_results=10,
                                        next_token=next_token)
        except TooManyRequests:
            sleep(1)
            continue

        call_count += 1

        if res.meta.get("result_count") == 0:
            break

        extract_info(res, results)

        if 'next_token' not in res.meta:
            break

        next_token = res.meta['next_token']

    return results


def test_query_results() -> list[dict]:
    users, keywords, hashtags, exclude, countries, languages, start_time, end_time = get_searching_config()

    query = build_query(keywords, hashtags, exclude, countries, languages)

    return test_search_tweets(query, start_time, end_time)
