import json
import os
import time
from urllib.parse import urlparse, urljoin, unquote

import chromedriver_autoinstaller
import regex as re
import requests
import spacy
import validators
from bs4 import BeautifulSoup
from gensim.parsing.preprocessing import remove_stopwords
from selenium import webdriver
from selenium.webdriver.chromium.options import ChromiumOptions as Options
from wordfreq import zipf_frequency

from crawler.utils import map_entity_to_name, filter_amp_data, \
    filter_meta_data, clean_text, FAKE_USER_AGENT
from utils.utils import standardize_url, normalize_unicode_text, link_belongs_to_domain, url_is_downloadable

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

        write_mode = "w" if os.path.exists(f'{filename}.json') else "x"

        with open(f'{filename}.json', write_mode) as f:
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

    @staticmethod
    def get_driver():
        options = Options()

        prefs = {
            "download_restrictions": 3,
        }

        options.headless = True
        options.add_argument("--enable-javascript")
        options.add_experimental_option("prefs", prefs)

        return webdriver.Chrome(options=options)

    def confirm_url(self, url):
        try:
            if self.crawl_javascript:
                driver = self.get_driver()

                head_req = requests.request("HEAD", url, headers={
                    'Accept-Language': 'en-US,en',
                    'User-Agent': FAKE_USER_AGENT
                }, timeout=self.SESSION_TIMEOUT, verify=self.VERIFY)
                status_code = head_req.status_code
                downloadable = url_is_downloadable(head_req.headers)

                # Sometimes HEAD request returns 4** error when GET returns 200
                if 400 <= status_code < 500:
                    head_req = requests.request("GET", url, headers={
                        'Accept-Language': 'en-US,en',
                        'User-Agent': FAKE_USER_AGENT
                    }, timeout=self.SESSION_TIMEOUT, verify=self.VERIFY)
                    status_code = head_req.status_code
                    downloadable = url_is_downloadable(head_req.headers)

                if downloadable:
                    return None, 406

                driver.get(url)

                source = driver.page_source

                driver.quit()
            else:
                response = requests.request("GET", url, headers={
                    'Accept-Language': 'en-US,en'
                }, timeout=self.SESSION_TIMEOUT, verify=self.VERIFY)
                status_code = response.status_code
                source = response.text
                downloadable = url_is_downloadable(response.headers)

                if downloadable:
                    return None, 406

                if status_code == 403 or status_code == 406:
                    response = requests.request("GET", url, headers={
                        'Accept-Language': 'en-US,en',
                        'User-Agent': FAKE_USER_AGENT
                    }, timeout=self.SESSION_TIMEOUT, verify=self.VERIFY)
                    status_code = response.status_code
                    source = response.text

        except Exception as e:
            if self.crawl_javascript and driver:
                driver.quit()

            print(e)
            return None, 404

        return source, status_code

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

        self.corpus += normalize_unicode_text(" " +
                                              ' '.join(soup_html.stripped_strings).lower())

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
            except Exception:
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
        url = unquote(url)
        domain_name = urlparse(url).hostname

        html, status_code = self.confirm_url(url)

        if status_code >= 400 or html is None:
            return []

        if '<html' not in html:
            html = re.sub(r'(?:<!DOCTYPE(?:\s\w)?>(?:<head>)?)',
                          '<!DOCTYPE html><html>', html)

        soup = BeautifulSoup(clean_text(html), "lxml")
        links = [unquote(link)
                 for link in self.get_website_links(domain_name, soup) if link is not None]

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

    @staticmethod
    def get_combinations(expressions):
        expressions = [re.sub(r"(\W|_)+", " ", expression.lower()).strip()
                       for expression in expressions]
        expression_combinations = set(expressions)
        token_combinations = set()
        weight_sum = 0

        for expression in expressions:
            expression_combinations.add(expression.replace("&", "and"))

        for expression in expression_combinations:
            tokens = expression.split(" ")

            if len(tokens) > 1:
                token_combinations.update(
                    [token for token in tokens if len(token) > 3])

        expression_tuples = []

        for expression in expression_combinations:
            length = len(expression)
            regex_expression = "(?b)(\\b" + expression.replace(" ",
                                                               "){e<=2}(\w){0,2}((\W|_)|(\W|_)(\w)*(\W|_)){0,2}(\w){0,2}(?b)(") + "\\b){e<=2}"

            expression_tuples.append((regex_expression, length, 1.0))
            weight_sum += 1.0

        for token in token_combinations:
            length = len(token)
            regex_expression = "(?b)(\\b" + token + "\\b){e<=1}"
            weight = 0.25 - (zipf_frequency(token, 'en') / 32.0)

            expression_tuples.append((regex_expression, length, weight))
            weight_sum += weight

        return [(expression, length, weight / weight_sum) for expression, length, weight in expression_tuples]

    @staticmethod
    def calculate_score(original_length, match_length, num_errors):
        abs_diff = abs(original_length - match_length)

        return original_length / (original_length + abs_diff + 2 * num_errors)

    def get_score(self, search_expression, length, string):
        match = re.search(search_expression, string)

        if match:
            # print(f"""
            #     The search expression:
            #         {search_expression}
            #     Matched with:
            #         {match[0]}
            #     Allowing the following errors:
            #         {match.fuzzy_changes}
            #     With a score of:
            #         {self.calculate_score(length, len(match[0]), sum(match.fuzzy_counts))}
            # """)

            return self.calculate_score(length, len(match[0]), sum(match.fuzzy_counts))

        return 0

    def get_expression_score(self, expression):
        search_expressions = self.get_combinations([expression])
        score = 0

        for search_expression, length, weight in search_expressions:
            matches = {
                "name": self.get_score(search_expression, length, self.name.lower()),
                "titles": self.get_score(search_expression, length, self.title.lower()),
                "description": self.get_score(search_expression, length, self.description.lower()),
                "keywords": self.get_score(search_expression, length, " ".join(self.keywords).lower()),
                "internal links": self.get_score(search_expression, length, " ".join(self.internal_links).lower()),
                "external links": self.get_score(search_expression, length, " ".join(self.external_links).lower()),
                "emails": self.get_score(search_expression, length, " ".join(self.emails).lower()),
                "corpus": self.get_score(search_expression, length, self.corpus.lower()),
            }

            # pprint(
            #     f"Search expression: {search_expression} with score {sum(matches.values()) * weight}")

            score += (sum(matches.values()) / 8.0) * weight

        return score

    def check_for_matches(self, search_words):
        match_scores = []

        for search_word in search_words:
            match_scores.append(self.get_expression_score(search_word))

        # pprint(match_scores)

        return match_scores

    def extract_entitites(self):
        start_time = time.time()
        nlp = spacy.load("en_core_web_sm",
                         disable=["tok2vec", "tagger", "parser", "attribute_ruler", "lemmatizer"])
        print("Load time: %s seconds" % (time.time() - start_time))

        entities = {
            "person": set(),
            "norp": set(),
            "fac": set(),
            "organization": set(),
            "location": set(),
            "places": set(),
            "product": set(),
            "event": set(),
            "art": set(),
            "law": set(),
            "language": set(),
            "date": set(),
            "time": set(),
            "percent": set(),
            "money": set(),
            "quantity": set(),
            "ordinal": set(),
            "cardinal": set()
        }

        doc = nlp(self.corpus)

        for entity in doc.ents:
            entities[map_entity_to_name(entity.label_)].add(entity.text)

        entities = {label: list(res) for label, res in entities.items()}

        with open(f'entities.json', "w") as f:
            json.dump(entities, f)
