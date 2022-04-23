import re
import os
import csv
import time
import json
import tweepy
import pickle
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
from gensim.parsing.preprocessing import remove_stopwords, strip_multiple_whitespaces
from selenium.webdriver.chromium.options import ChromiumOptions as Options
from multiprocessing import get_context


api = tweepy.Client(
    bearer_token='AAAAAAAAAAAAAAAAAAAAADTxXwEAAAAApg4qeQrET9wiXNc8VqrxZF9aK%2Bs%3DT04MJA4P6nj14b41JzTfivhlWICAtQhmzO6XxvQipxISmh5pcS')


def test_crawler(handle, url):
    domain_name = urlparse(url).netloc
    filename = f"websites/{handle}_{domain_name}"

    if os.path.exists(f"{filename}.json"):
        return

    try:
        cwlr = Crawler(crawl_javascript=False)
        cwlr.crawl(url)
        cwlr.save_state(filename)
        print(f" · Finished crawling {url} ·")
    except Exception as e:
        print(f"Issue crawling {url}: {e}")


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def process_username(username):
    username = unicodedata.normalize("NFKD", username).encode(
        "ascii", errors='ignore').decode()

    username = re.sub(r"\(.*\)", "", username)
    username = re.sub(r"(#|@)\w*\b", "", username)
    username = re.sub(r"\|", "", username)

    return strip_multiple_whitespaces(username)


def batch_request(twitter_handles):
    users = api.get_users(usernames=twitter_handles).data

    res = {}

    for user in users:
        res[user['username']] = process_username(user["name"])

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

        with open("handle_mapping.json", 'w') as fp:
            json.dump(mapping, fp)


def save_websites():
    with open("sources/websites_dataset.csv", 'r', encoding='UTF8') as f:
        reader = csv.reader(f)
        next(reader)

        # with get_context("spawn").Pool() as pool:
        #     for [handle, website] in reader:
        #         pool.apply_async(test_crawler, (handle, website))

        pool = get_context("spawn").Pool()

        for [handle, website] in reader:
            # if not os.path.exists(f"websites/{handle}_{urlparse(website).netloc}.json"):
            #     print(f"{handle}: {website}")
            pool.apply_async(test_crawler, (handle, website))

        pool.close()
        pool.join()


def main():
    start_time = time.time()
    save_websites()
    # test_crawler("test", "https://karlrecords.bandcamp.com/")

    print("Elapsed time: %s seconds" % (time.time() - start_time))


if __name__ == '__main__':
    main()
