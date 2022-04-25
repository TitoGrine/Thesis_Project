# import re
import time
import json
import random
import pickle
import requests
import operator
import functools
import validators
import regex as re
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

from .utils import standardize_url, filter_amp_data, filter_meta_data, clean_text, link_belongs_to_domain

chromedriver_autoinstaller.install()


class Crawler:
    SESSION_TIMEOUT = 30
    VERIFY = False
    REJECT_TYPES = ["favicon", "twitter:image"]
    SPECIAL_CRAWLING = ["linktr.ee", "lnk.to", "ampl.ink",
                        "biglink.to", "linkgenie.co", "allmylinks.com", "withkoji.com"]

    def __init__(self, state_file=None, crawl_javascript=False, max_urls=15):
        self.crawl_javascript = crawl_javascript
        self.max_urls = max_urls
        self.total_urls_visited = 0

        if state_file is not None:
            self.load_state(state_file)
        else:
            self.initialize_state()

    def save_state(self, filename):
        state = {
            "original_url": self.original_url,
            "name": self.name.lower(),
            "title": self.title.lower(),
            "description": self.description.lower(),
            "keywords": self.keywords,
            "internal_links": list(self.internal_links),
            "external_links": list(self.external_links),
            "emails": list(self.emails),
            "phone_numbers": list(self.phone_numbers),
            "images": self.images,
            "corpus": self.corpus.lower(),
            "is_link_tree": self.is_link_tree,
        }

        with open(f'{filename}.json', 'x') as f:
            json.dump(state, f)

    def load_state(self, state_file):
        with open(f'{state_file}.json', 'r') as f:
            state = json.load(f)

            try:
                self.original_url = state["original_url"]
                self.name = state["name"]
                self.title = state["title"]
                self.description = state["description"]
                self.internal_links = state["internal_links"]
                self.external_links = state["external_links"]
                self.keywords = state["keywords"]
                self.emails = state["emails"]
                self.phone_numbers = state["phone_numbers"]
                self.corpus = state["corpus"]
                self.images = state["images"]
                self.is_link_tree = state["is_link_tree"]
            except Exception as e:
                print(f"Error loading state: {e}")

    def initialize_state(self):
        self.original_url = ""
        self.name = ""
        self.title = ""
        self.description = ""
        self.corpus = ""
        self.keywords = []
        self.images = []
        self.is_link_tree = False

        self.internal_links = set()
        self.external_links = set()
        self.emails = set()
        self.phone_numbers = set()

    def get_driver(self):
        options = Options()

        options.headless = True
        options.add_argument("--enable-javascript")

        return webdriver.Chrome(options=options)

    def confirm_url(self, url):
        try:
            if self.crawl_javascript:
                driver = self.get_driver()
                driver.get(url)

                head_req = requests.head(url)
                status_code = head_req.status_code
                source = driver.page_source

                driver.quit()
            else:
                response = requests.request("GET", url, headers={
                    'Accept-Language': 'en-US,en'
                }, timeout=self.SESSION_TIMEOUT, verify=self.VERIFY)
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

    def save_corpus(self, soup_html):
        for s in soup_html(['script', 'style']):
            s.decompose()

        self.corpus += " " + ' '.join(soup_html.stripped_strings).lower()

    def get_website_links(self, domain, soup):
        if domain not in self.SPECIAL_CRAWLING:
            return [tag.attrs.get("href") for tag in soup.find_all(["a"])]
        else:
            self.is_link_tree = True

        if "linktr.ee" in domain:
            script_contents = soup.find(id="__NEXT_DATA__").contents

            try:
                return [link["url"] for link in json.loads(script_contents[0])[
                    "props"]["pageProps"]["account"]["links"] if "url" in link]
            except Exception as e:
                return []
        elif "biglink.to" in domain or "withkoji.com" in domain:
            return []
        elif "lnk.to" in domain or "ampl.ink" in domain:
            return [tag.attrs.get("href") for tag in soup.find_all(["a"])]
        elif "linkgenie.co" in domain:
            linkgenie_links = [tag.attrs.get("href")
                               for tag in soup.find_all(["a"])]

            return [requests.get(link).url for link in linkgenie_links]
        elif "allmylinks.com" in domain:
            return [tag.attrs.get("title") for tag in soup.find_all(["a"])]

    def parse_website(self, url):
        """
        Returns all URLs that is found on `url` in which it belongs to the same website
        """
        # all URLs of `url`
        urls = set()
        # domain name of the URL without the protocol
        domain_name = urlparse(url).hostname

        html = self.confirm_url(url)

        if html is None:
            if url in self.internal_links:
                self.internal_links.remove(url)
            return []

        if '<html' not in html:
            html = re.sub(r'(?:<!DOCTYPE(?:\s\w)?>(?:<head>)?)',
                          '<!DOCTYPE html><html>', html)

        soup = BeautifulSoup(clean_text(html), "lxml")
        links = self.get_website_links(domain_name, soup)

        description, keywords, title = filter_meta_data(soup, url)
        self.save_title(title)
        self.save_description(description)
        self.save_keywords(keywords)

        name, title, images = filter_amp_data(soup, url)
        self.save_corpus(soup)
        self.save_name(name)
        self.save_title(title)
        self.save_images(images)

        for link in links:
            if link is None:
                continue

            link = link.strip()

            if link.find('mailto:') > -1:
                email = link.split(":")[1]
                if link not in self.emails and validators.email(email):
                    self.emails.add(email)
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

            if not validators.url(link):
                # not a valid URL
                continue
            if link in self.internal_links:
                # already in the set
                continue

            if not link_belongs_to_domain(link, domain_name):
                # external link
                if link not in self.external_links:
                    self.external_links.add(link)
                continue

            urls.add(link)
            self.internal_links.add(link)

        return urls

    def check_external_links(self):
        external_links = self.external_links

        self.external_links = filter(validators.url, self.external_links)

    def crawl_helper(self, url):
        if self.total_urls_visited >= self.max_urls:
            return

        self.total_urls_visited += 1

        for link in self.parse_website(url):
            self.crawl_helper(link)

    def crawl(self, url):
        self.original_url = url
        self.internal_links.add(standardize_url(url))

        self.crawl_helper(url)

        self.check_external_links()

    def get_combinations(self, terms):
        # strip_chars = " -_"
        terms = [re.sub(r"(\W|_)+", " ", term.lower()).strip()
                 for term in terms]
        term_comb = set(terms)

        for term in terms:
            term_comb.add(term.replace("&", "and"))

        term_tuples = []

        # Dictionary with regex and the number of chars

        for term in term_comb:
            size = len(term)
            regex_term = "(?b)(\\b" + term.replace(" ",
                                                   "){e<=2}(\w){0,2}((\W|_)|(\W|_)(\w)*(\W|_)){0,2}(\w){0,2}(?b)(") + "\\b){e<=2}"

            term_tuples.append((regex_term, size))

        return term_tuples

    def calculate_score(self, original_length, match_length, num_errors):
        abs_diff = abs(original_length - match_length)

        return original_length / (original_length + abs_diff + num_errors)

    def get_score(self, search_term, length, string):
        match = re.search(search_term, string)

        if match:
            #         print(f"""
            # The search term:
            #     {search_term}
            # Matched with:
            #     {match[0]}
            # Allowing the following errors:
            #     {match.fuzzy_changes}
            # With a score of:
            #     {self.calculate_score(length, len(match[0]), sum(match.fuzzy_counts))}
            #         """)

            return self.calculate_score(length, len(match[0]), sum(match.fuzzy_counts))

        return 0

    def check_for_matches(self, terms):
        search_terms = self.get_combinations(terms)
        match_scores = []

        for search_term, length in search_terms:

            matches = {
                "name": self.get_score(search_term, length, self.name.lower()),
                "titles": self.get_score(search_term, length, self.title.lower()),
                "description": self.get_score(search_term, length, self.description.lower()),
                "internal links": self.get_score(search_term, length, " ".join(self.internal_links).lower()),
                "external links": self.get_score(search_term, length, " ".join(self.external_links).lower()),
                "emails": self.get_score(search_term, length, " ".join(self.emails).lower()),
                "corpus": self.get_score(search_term, length, self.corpus.lower()),
            }

            match_scores.append(sum(matches.values()))
            # pprint(matches)

        pprint(match_scores)

        return match_scores
