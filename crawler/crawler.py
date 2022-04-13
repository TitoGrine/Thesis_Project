import requests
import re
import random
import time
import functools
import operator
import json
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chromium.options import ChromiumOptions as Options

from lassie import Lassie
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor
from pprint import pprint
from urllib.parse import urlparse, urljoin, quote
from bs4 import BeautifulSoup, SoupStrainer
from gensim.parsing.preprocessing import remove_stopwords

from .utils import standardize_url, active_url, filter_amp_data, filter_meta_data, clean_text

chromedriver_autoinstaller.install()


class Crawler:
    SESSION_TIMEOUT = 5
    REJECT_TYPES = ["favicon", "twitter:image"]
    SPECIAL_CRAWLING = ["linktr.ee", "lnk.to",
                        "biglink.to", "linkgenie.co", "allmylinks.com", "withkoji.com"]

    internal_urls = set()
    external_urls = set()
    emails = set()
    phone_numbers = set()

    def __init__(self, crawl_javascript=False, max_urls=15):
        self.max_urls = max_urls
        self.total_urls_visited = 0
        self.description = ""
        self.keywords = []
        self.images = []
        self.name = ""
        self.title = ""
        self.text = ""
        self.is_link_tree = False
        self.crawl_javascript = crawl_javascript

    def get_session(self):
        session = requests.Session()
        session.timeout = self.SESSION_TIMEOUT

        return session

    def is_valid(self, url):
        """
        Checks whether `url` is a valid URL.
        """
        parsed = urlparse(url)

        return bool(parsed.netloc) and bool(parsed.scheme)

    def get_driver(self):
        options = Options()

        options.headless = True
        options.add_argument("--enable-javascript")

        return webdriver.Chrome(options=options)

    def confirm_url(self, url):
        try:
            # response = self.lassie.fetch(
            #     url, twitter_card=False, touch_icon=False, favicon=False)

            if self.crawl_javascript:
                driver = self.get_driver()
                driver.get(url)

                head_req = requests.head(url)
                status_code = head_req.status_code
                source = driver.page_source

                driver.quit()
            else:
                response = requests.get(url, headers={
                    'Accept-Language': 'en-US,en'
                })
                status_code = response.status_code
                source = response.text

        except Exception as e:
            if self.crawl_javascript:
                driver.quit()

            print(e)
            return None

        if status_code >= 400:
            return None

        return source

    def save_images(self, images):
        if images and len(images) > 0:
            self.images.extend(
                filter(lambda img: "type" not in img or img["type"] not in self.REJECT_TYPES, images))

    def save_keywords(self, keywords):
        if keywords and len(keywords) > 0:
            self.keywords.extend(keywords)

    def save_description(self, description):
        if len(description) > 0:
            self.description += " " + remove_stopwords(description)

    def save_name(self, name):
        if name and len(name) > 0:
            self.name = name

    def save_title(self, title):
        if title and len(title) > 0:
            self.title += " " + title

    def save_text(self, soup_html):
        for s in soup_html(['script', 'style']):
            s.decompose()

        self.text += " " + \
            remove_stopwords(' '.join(soup_html.stripped_strings))

    def get_website_links(self, domain, soup):
        if domain not in self.SPECIAL_CRAWLING:
            return [tag.attrs.get("href") for tag in soup.find_all(["a"])]
        else:
            self.is_link_tree = True

        if domain == "linktr.ee":
            script_contents = soup.find(id="__NEXT_DATA__").contents

            try:
                return [link["url"] for link in json.loads(script_contents[0])[
                    "props"]["pageProps"]["account"]["links"] if "url" in link]
            except Exception as e:
                return []
        elif domain == "biglink.to" or domain == "withkoji.com":
            return []
        elif domain == "lnk.to":
            return [tag.attrs.get("href") for tag in soup.find_all(["a"])]
        elif domain == "linkgenie.co":
            linkgenie_links = [tag.attrs.get("href")
                               for tag in soup.find_all(["a"])]

            return [self.get_session().get(link).url for link in linkgenie_links]
        elif domain == "allmylinks.com":
            return [tag.attrs.get("title") for tag in soup.find_all(["a"])]

    def parse_website(self, url):
        """
        Returns all URLs that is found on `url` in which it belongs to the same website
        """
        # all URLs of `url`
        urls = set()
        # domain name of the URL without the protocol
        domain_name = urlparse(url).netloc

        html = self.confirm_url(url)

        if html is None:
            if url in self.internal_urls:
                self.internal_urls.remove(url)
            return []

        if '<html' not in html:
            html = re.sub(r'(?:<!DOCTYPE(?:\s\w)?>(?:<head>)?)',
                          '<!DOCTYPE html><html>', html)

        soup = BeautifulSoup(clean_text(html), "lxml")
        links = self.get_website_links(domain_name, soup)

        description, keywords = filter_meta_data(soup, url)
        name, title, images = filter_amp_data(soup, url)
        self.save_text(soup)
        self.save_name(name)
        self.save_title(title)
        self.save_images(images)
        self.save_keywords(keywords)
        self.save_description(description)

        for link in links:
            if link is None:
                continue

            link = link.strip()

            if link.find('mailto:') > -1:
                if link not in self.emails:
                    self.emails.add(link.split(":")[1])
                continue

            if link.find('tel:') > -1:
                if link not in self.phone_numbers:
                    self.phone_numbers.add(link.split(":")[1])
                continue

            # join the URL if it's relative (not absolute link)
            link = urljoin(url, link)
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
        if self.total_urls_visited > self.max_urls:
            return []

        self.total_urls_visited += 1

        for link in self.parse_website(url):
            self.crawl_helper(link)

    def crawl(self, url):
        self.internal_urls.add(standardize_url(url))

        self.crawl_helper(url)

        self.check_external_urls()

    def get_combinations(self, words):
        strip_chars = " -_"
        words = [word.lower().strip(strip_chars).replace("|", "")
                 for word in words]
        word_comb = set(words)

        for word in words:
            word_comb.add(word.replace(" ", "-").strip(strip_chars))
            word_comb.add(word.replace(" ", "_").strip(strip_chars))
            word_comb.add(word.replace(" ", "").strip(strip_chars))
            word_comb.add(word.replace("_", "-").strip(strip_chars))
            word_comb.add(word.replace("_", " ").strip(strip_chars))
            word_comb.add(word.replace("_", "").strip(strip_chars))
            word_comb.add(word.replace("-", "_").strip(strip_chars))
            word_comb.add(word.replace("-", " ").strip(strip_chars))
            word_comb.add(word.replace("-", "").strip(strip_chars))

        return word_comb

    def check_for_matches(self, words):
        word_comb = self.get_combinations(words)
        pattern = re.compile("|".join(word_comb))

        matches = {
            "name": bool(re.search(pattern, (self.name.lower()))),
            "titles": bool(re.search(pattern, (self.title.lower()))),
            "description": bool(re.search(pattern, (self.description.lower()))),
            "internal links": True in (re.search(pattern, link.lower()) for link in self.internal_urls),
            "external links": True in (re.search(pattern, link.lower()) for link in self.external_urls),
            "emails": True in (re.search(pattern, email.lower()) for email in self.emails),
            "corpus": bool(re.search(pattern, (self.text.lower()))),
        }

        pprint(matches)

    def save_state(self):
        state = {
            "Name": self.name.lower(),
            "Titles": self.title.lower(),
            "Description": self.description.lower(),
            "Keywords": self.keywords,
            "Link Tree": self.is_link_tree,
            "Total Internal links": list(self.internal_urls),
            "Total External links": list(self.external_urls),
            "Total Emails": list(self.emails),
            "Total Phone Numbers": list(self.phone_numbers),
            "Images": self.images,
            "Text": self.text.lower()
        }

        with open(f'./test.json', 'w') as f:
            json.dump(state, f)
