import re

# General constants
CONFIG_FILE = "config.json"
SECTIONS = ["searching", "discovery", "extraction"]
OUTPUT_DIR = "output"
PROFILE_INFO_FILE = "profile_info.json"
ES_ENDPOINT = "https://localhost:9200"
ES_INDEX_CONFIG = "searches"
ES_INDEX_SEARCH = "search"
PROFILE_FIELDS = ["username", "name", "location", "description", "entities"]
NORMAL_LINK_FIELDS = ["name", "title", "description", "keywords", "phone_numbers"]
WILDCARD_LINK_FIELDS = ["original_link", "emails"]

# Discovery constants
TOPIC_SIMILARITY_THRESHOLD = 0.275
MAX_ATTEMPTS = 5
WORD_MODEL = "word2vec-google-news-300"
USER_FIELDS = ["description", "entities", "location", "name", "username", "profile_image_url"]
REFUSE_DOMAINS = ["twitter.com"]
TWEET_FIELDS = ["text", "author_id", "context_annotations",
                "entities", "lang", "referenced_tweets"]

# Extraction constants
WEBSITE_RELATEDNESS_THRESHOLD = 0.075
MAX_CRAWL_DEPTH = 5
CLEANER = re.compile(r'[\r\n\t]')
RE_INT = re.compile(r'\d+')
FAKE_USER_AGENT = 'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Chrome/41.0.2272.96 Safari/537.36'
SESSION_TIMEOUT = 15
CERTIFICATE_VERIFY = True
REJECT_TYPES = ["favicon", "twitter:image"]
SPECIAL_CRAWLING = ["linktr.ee", "lnk.to", "ampl.ink",
                    "biglink.to", "linkgenie.co", "allmylinks.com", "withkoji.com"]
ENTITY_MAP = {
    "PERSON": "person",
    "NORP": "norp",
    "FAC": "fac",
    "ORG": "organization",
    "GPE": "location",
    "LOC": "places",
    "PRODUCT": "product",
    "EVENT": "event",
    "WORK_OF_ART": "art",
    "LAW": "law",
    "LANGUAGE": "language",
    "DATE": "date",
    "TIME": "time",
    "PERCENT": "percent",
    "MONEY": "money",
    "QUANTITY": "quantity",
    "ORDINAL": "ordinal",
    "CARDINAL": "cardinal"
}
DOWNLOADABLE_FORMATS = ['audio', 'video', 'image', 'font', 'application/gzip', 'application/vnd.rar',
                        'application/x-7z-compressed',
                        'application/zip', 'application/x-tar', 'application/pdf', 'text/csv']
