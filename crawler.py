import requests
import re
import random

from pprint import pprint
from urllib.parse import urlparse, urljoin, quote
from bs4 import BeautifulSoup


def standardize_url(url):
    return url[:-1] + url[-1:].replace("/", "")


def active_url(url):
    try:
        response = requests.head(url)

        if response.status_code >= 400:
            return False
    except:
        return False

    return True


class Crawler:
    internal_urls = set()
    external_urls = set()
    emails = set()
    phone_numbers = set()

    def get_proxies(self):
        url = "https://free-proxy-list.net/"
        # get the HTTP response and construct soup object
        soup = BeautifulSoup(requests.get(url).content, "lxml")
        proxies = []
        for row in soup.find("div", {"class": "fpl-list"}).find_all("tr")[1:30]:
            tds = row.find_all("td")
            try:
                ip = tds[0].text.strip()
                port = tds[1].text.strip()
                host = f"{ip}:{port}"
                proxies.append(host)
            except IndexError:
                continue

        self.proxies = proxies

    def __init__(self, max_urls=50):
        self.max_urls = max_urls
        self.total_urls_visited = 0
        self.get_proxies()

    def get_session(self):
        # construct an HTTP session
        session = requests.Session()
        # choose one random proxy
        proxy = random.choice(self.proxies)
        # session.proxies = {"http": proxy, "https": proxy}
        session.timeout = 5

        return session

    def is_valid(self, url):
        """
        Checks whether `url` is a valid URL.
        """
        parsed = urlparse(url)

        return bool(parsed.netloc) and bool(parsed.scheme)

    def confirm_url(self, url):
        try:
            response = self.get_session().get(url)
        except Exception as e:
            print(e)
            return None

        if response.status_code >= 400:
            return None

        return response

    def get_all_website_links(self, url):
        """
        Returns all URLs that is found on `url` in which it belongs to the same website
        """
        # all URLs of `url`
        urls = set()
        # domain name of the URL without the protocol
        domain_name = urlparse(url).netloc

        response = self.confirm_url(url)

        if response is None:
            if url in self.internal_urls:
                self.internal_urls.remove(url)
            return []

        soup = BeautifulSoup(response.content, "lxml")

        for a_tag in soup.find_all("a"):
            href = a_tag.attrs.get("href")
            if href == "" or href is None:
                # href empty tag
                continue

            href = href.strip()

            if href.find('mailto:') > -1:
                if href not in self.emails:
                    self.emails.add(href.split(":")[1])
                continue

            # join the URL if it's relative (not absolute link)
            link = urljoin(url, href)
            parsed_link = urlparse(link)
            # remove URL GET parameters, URL fragments, etc.
            link = parsed_link.scheme + "://" + parsed_link.netloc + parsed_link.path
            link = standardize_url(link)

            if not self.is_valid(link):
                # not a valid URL
                continue
            if link in self.internal_urls:
                # already in the set
                continue
            if domain_name not in link:
                # external link
                if link not in self.external_urls:
                    self.external_urls.add(link)
                continue

            urls.add(link)
            self.internal_urls.add(link)

        return urls

    def check_external_urls(self):
        external_urls = self.external_urls

        self.external_urls = filter(active_url, self.external_urls)

    def crawl_helper(self, url):
        self.total_urls_visited += 1
        links = self.get_all_website_links(url)
        for link in links:
            if self.total_urls_visited > self.max_urls:
                break
            self.crawl_helper(link)

    def crawl(self, url):
        self.internal_urls.add(standardize_url(url))

        self.crawl_helper(url)

        self.check_external_urls()

    def get_state(self):
        return {
            "Total Internal links": list(self.internal_urls),
            "Total External links": list(self.external_urls),
            "Total Emails": list(self.emails),
            "Total Phone Numbers": list(self.phone_numbers)
        }
