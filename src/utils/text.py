import re
import unicodedata

from gensim.parsing import preprocessing


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


def normalize_unicode_text(text):
    return unicodedata.normalize("NFKD", text).encode(
        "ascii", errors='ignore').decode()
