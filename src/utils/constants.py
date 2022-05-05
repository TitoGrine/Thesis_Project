# General constants
CONFIG_FILE = "config.json"
SECTIONS = ["searching", "discovery", "extraction"]
OUTPUT_DIR = "output"

# Discovery constants
TOPIC_SIMILARITY_THRESHOLD = 0.275
WORD_MODEL = "word2vec-google-news-300"
USER_FIELDS = ["description", "entities", "location", "name", "username", "profile_image_url"]
REFUSE_DOMAINS = ["twitter.com"]
TWEET_FIELDS = ["text", "author_id", "context_annotations",
                "entities", "lang", "referenced_tweets"]

# Extraction constants
DOWNLOADABLE_FORMATS = ['audio', 'video', 'image', 'font', 'application/gzip', 'application/vnd.rar',
                        'application/x-7z-compressed',
                        'application/zip', 'application/x-tar', 'application/pdf', 'text/csv']
