import re
import csv
import time
import json
import tweepy
import requests
import unicodedata
from pprint import pprint
from lassie import Lassie
from bs4 import BeautifulSoup
from selenium import webdriver
from crawler.crawler import Crawler
from requests_html import HTMLSession
from trafilatura import fetch_url, extract
from trafilatura.spider import focused_crawler
from urllib.parse import urlparse, urljoin, quote
from gensim.parsing.preprocessing import remove_stopwords
from selenium.webdriver.chromium.options import ChromiumOptions as Options


api = tweepy.Client(
    bearer_token='AAAAAAAAAAAAAAAAAAAAADTxXwEAAAAApg4qeQrET9wiXNc8VqrxZF9aK%2Bs%3DT04MJA4P6nj14b41JzTfivhlWICAtQhmzO6XxvQipxISmh5pcS')


def test_crawler(with_selenium=False):
    cwlr = Crawler(crawl_javascript=with_selenium)

    start_time = time.time()
    cwlr.crawl('http://linktr.ee/allierougeot')
    cwlr.check_for_matches(["Allie Rougeot", "AlienorR2"])
    cwlr.save_state()
    print("Elapsed time: %s seconds" % (time.time() - start_time))


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def batch_request(twitter_handles):
    users = api.get_users(usernames=twitter_handles).data

    res = {}

    for user in users:
        res[user['username']] = unicodedata.normalize(
            "NFKD", user['name'].decode("utf8", errors='replace'))

    return res


def save_states():
    with open("sources/websites_dataset.csv", 'r', encoding='UTF8') as f:
        reader = csv.reader(f)
        next(reader)

        handles = set()

        for [handle, website] in reader:
            handles.add(handle)

        handles_chunks = list(chunks(list(handles), 100))

        mapping = {}

        for chunk in handles_chunks:
            mapping.update(batch_request(chunk))

        with open("handle_mapping.json", 'x') as fp:
            json.dump(mapping, fp)


def main():
    save_states()


if __name__ == '__main__':
    main()
