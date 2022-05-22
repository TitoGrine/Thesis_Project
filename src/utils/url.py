import re

from urllib.parse import urlparse
from .constants import DOWNLOADABLE_FORMATS


def standardize_url(url):
    url = url.strip()

    return url[:-1] + url[-1:].replace("/", "")


def link_from_host(link, host):
    link_host = urlparse(link).hostname

    return bool(re.search(r"(?:[^/:]+\.)?" + host, link_host)) or bool(
        re.search(r"(?:[^/:]+\.)?" + link_host, host))


def url_is_dowloadable_partial_check(url):
    exclude_extensions = re.compile(r"(pdf|jpeg|jpg|png|gif|svg|zip|exe)(/)?$")

    stripped_url = remove_url_query(url)

    return bool(exclude_extensions.search(stripped_url))


def url_is_downloadable(headers):
    Content_Type = headers.get("Content-Type", "")

    return bool([file_format for file_format in DOWNLOADABLE_FORMATS if file_format in Content_Type])


def remove_url_query(url):
    url = standardize_url(url)

    parsed_url = urlparse(url)

    return f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
