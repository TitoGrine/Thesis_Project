import re

from urllib.parse import urlparse
from .constants import DOWNLOADABLE_FORMATS


def standardize_url(url):
    return url[:-1] + url[-1:].replace("/", "")


def link_belongs_to_domain(link, domain):
    link_domain = urlparse(link).hostname

    return bool(re.search(r"(?:[^/:]+\.)?" + domain, link_domain)) or bool(
        re.search(r"(?:[^/:]+\.)?" + link_domain, domain))


def url_is_downloadable(headers):
    Content_Type = headers.get("Content-Type", "")

    return bool([file_format for file_format in DOWNLOADABLE_FORMATS if file_format in Content_Type])
