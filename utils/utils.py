import re
import unicodedata
from urllib.parse import urlparse

from gensim.parsing import preprocessing, strip_multiple_whitespaces

from crawler.utils import DOWNLOADABLE_FORMATS


def standardize_url(url):
    return url[:-1] + url[-1:].replace("/", "")


def normalize_unicode_text(text):
    return unicodedata.normalize("NFKD", text).encode(
        "ascii", errors='ignore').decode()


def link_belongs_to_domain(link, domain):
    link_domain = urlparse(link).hostname

    return bool(re.search(r"(?:[^/:]+\.)?" + domain, link_domain)) or bool(
        re.search(r"(?:[^/:]+\.)?" + link_domain, domain))


def url_is_downloadable(headers):
    Content_Type = headers.get("Content-Type", "")

    return bool([file_format for file_format in DOWNLOADABLE_FORMATS if file_format in Content_Type])


def remove_urls(tweet): return re.sub(
    r'(https?:\/\/)(\s)*(www\.)?(\s)*((\w|\s)+\.)*([\w\-\s]+\/)*([\w\-]+)((\?)?[\w\s]*=\s*[\w\%&]*)*', "", tweet,
    flags=re.MULTILINE)


def remove_mentions(tweet): return re.sub(
    r'@\w+', "", tweet, flags=re.MULTILINE)


def remove_retweet_tag(tweet): return re.sub(
    r'(^|\b)RT\b', "", tweet, flags=re.MULTILINE)


def remove_sanitized_chars(tweet): return re.sub(
    r'&\w+', "", tweet, flags=re.MULTILINE)


def remove_short(tweet): return preprocessing.strip_short(tweet, minsize=3)


def process_twitter_text(text):
    text = normalize_unicode_text(text)

    return preprocessing.preprocess_string(text, filters=[
        remove_urls, remove_sanitized_chars, remove_retweet_tag, remove_mentions, str.lower,
        preprocessing.strip_tags, preprocessing.strip_punctuation, preprocessing.strip_numeric,
        preprocessing.strip_non_alphanum, preprocessing.strip_multiple_whitespaces, preprocessing.remove_stopwords,
        preprocessing.strip_short])


def process_twitter_name(name):
    name = normalize_unicode_text(name)

    name = re.sub(r"\(.*\)", "", name)
    name = re.sub(r"([#@])\w*\b", "", name)
    name = re.sub(r"\|", "", name)

    return strip_multiple_whitespaces(name).strip()
