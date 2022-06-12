# Constants
from .constants import *
from .mapping import *

# General purpose util functions
from .general import chunks, merge_docs, flatten

# Util function for dealing with URLs
from .url import standardize_url, link_from_host, url_is_downloadable, remove_url_query, url_is_dowloadable_partial_check

# Util functions for filtering elements in text
from .text import normalize_unicode_text, remove_urls, remove_mentions, remove_retweet_tag, remove_sanitized_chars, \
    remove_short

# Util functions for Twitter elements
from .twitter import valid_tweet, get_retweet_id, process_twitter_text, process_twitter_name

# Functions to deal with the configuration file
from .config import get_searching_config, get_discovery_config, get_extraction_config

# Functions for crawling
from .crawler import get_driver, clean_html

# Functions modified from Lassie
from .lassie import filter_meta_data, filter_amp_data

# Functions for website data extraction
from .extraction import map_entity_to_name

# Functions for elasticsearch
from .elastic import connect_elasticsearch, save_search_result

# Functions related to time
from .time import print_elapsed_time

# Functions related to fuzzy matching
from .fuzziness import get_fuzziness_distance
