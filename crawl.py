import time
import requests
import json
import chromedriver_autoinstaller
import re
from requests_html import HTMLSession
from pprint import pprint
from lassie import Lassie
from bs4 import BeautifulSoup
from gensim.parsing.preprocessing import remove_stopwords
from crawler.crawler import Crawler
from trafilatura import fetch_url, extract
from trafilatura.spider import focused_crawler
from urllib.parse import urlparse, urljoin, quote
from selenium import webdriver
from selenium.webdriver.chromium.options import ChromiumOptions as Options


chromedriver_autoinstaller.install()


def test_crawler():
    cwlr = Crawler(crawl_javascript=False)

    start_time = time.time()
    # cwlr.crawl('https://biglink.to/faDS')
    # cwlr.crawl('https://greengenerationinitiative.org/about/')
    cwlr.crawl("https://linkgenie.co/Jessicakes33")
    # cwlr.crawl("https://allmylinks.com/lunalovelyx")
    # cwlr.crawl("https://withkoji.com/@piperrockelle")
    cwlr.save_state()
    print("Elapsed time: %s seconds" % (time.time() - start_time))


def lassie_test():
    with open(f'lassie.json', 'w') as f:
        l = Lassie()
        l.request_opts = {
            'headers': {
                'Accept-Language': 'en-US,en'
            }
        }
        l.parser = "lxml"

        lassie_res = l.fetch("https://linkgenie.co/Jessicakes33")

        json.dump(lassie_res, f)

        with open("output.html", "w") as file:
            file.write(str(lassie_res["html"]))


def test_selenium():
    with open("output.html", "w") as file:
        options = Options()

        options.headless = True
        options.add_argument("--enable-javascript")

        driver = webdriver.Chrome(options=options)

        driver.get('https://biglink.to/faDS')

        # print(res.html.html.links)

        soup = BeautifulSoup(driver.page_source, "lxml")

        scripts = soup(text=re.compile(r'window\.preloadLink = \{.*\}'))

        print(scripts)

        file.write(str(driver.page_source))

        driver.quit()


def main():
    if not False:
        test_crawler()
    else:
        lassie_test()


if __name__ == '__main__':
    main()
