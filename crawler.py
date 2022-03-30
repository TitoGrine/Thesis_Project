import requests
import re
from pprint import pprint
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup


class Crawler:
    internal_urls = set()
    external_urls = set()
    emails = set()
    phone_numbers = set()

    def __init__(self, max_urls=50):
        self.max_urls = max_urls
        self.total_urls_visited = 0

    def is_valid(self, url):
        """
        Checks whether `url` is a valid URL.
        """
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)

    def get_all_website_links(self, url):
        """
        Returns all URLs that is found on `url` in which it belongs to the same website
        """
        # all URLs of `url`
        urls = set()
        # domain name of the URL without the protocol
        domain_name = urlparse(url).netloc
        soup = BeautifulSoup(requests.get(url).content, "lxml")

        for a_tag in soup.find_all("a"):
            href = a_tag.attrs.get("href")
            if href == "" or href is None:
                # href empty tag
                continue

            if href.find('tel:') > -1:
                self.phone_numbers.add(href.split(":")[1])
                continue

            if href.find('mailto:') > -1:
                self.emails.add(href.split(":")[1])
                continue

            # join the URL if it's relative (not absolute link)
            href = urljoin(url, href)
            parsed_href = urlparse(href)
            # remove URL GET parameters, URL fragments, etc.
            href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path

            if not self.is_valid(href):
                # not a valid URL
                continue
            if href in self.internal_urls:
                # already in the set
                continue
            if domain_name not in href:
                # external link
                if href not in self.external_urls:
                    self.external_urls.add(href)
                continue

            urls.add(href)
            self.internal_urls.add(href)

        return urls

    def crawl(self, url):
        """
        Crawls a web page and extracts all links.
        You'll find all links in `external_urls` and `internal_urls` global set variables.
        params:
            max_urls (int): number of max urls to crawl, default is 30.
        """
        self.total_urls_visited += 1
        links = self.get_all_website_links(url)
        for link in links:
            if self.total_urls_visited > self.max_urls:
                break
            self.crawl(link)

    def print_state(self):
        print("Total Internal links:")
        pprint(self.internal_urls)
        print("Total External links:")
        pprint(self.external_urls)
        print("Total Emails:")
        pprint(self.emails)
        print("Total Phone Numbers:")
        pprint(self.phone_numbers)
