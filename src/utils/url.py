import re

from urllib.parse import urlparse, urljoin
from .constants import DOWNLOADABLE_FORMATS


def standardize_url(url):
    url = url.strip()

    return url[:-1] + url[-1:].replace("/", "")


def link_from_host(link, host):
    link_host = urlparse(link).hostname

    return bool(re.search(r"(?:[^/:]+\.)?" + host, link_host)) or bool(
        re.search(r"(?:[^/:]+\.)?" + link_host, host))


def url_is_downloadable(headers):
    Content_Type = headers.get("Content-Type", "")

    return bool([file_format for file_format in DOWNLOADABLE_FORMATS if file_format in Content_Type])
