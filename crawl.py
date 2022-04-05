import time
import json
from pprint import pprint
from lassie import Lassie
from bs4 import BeautifulSoup
from gensim.parsing.preprocessing import remove_stopwords
from crawler import Crawler
from trafilatura import fetch_url, extract
from trafilatura.spider import focused_crawler


def test_crawler():
    cwlr = Crawler()

    cwlr.crawl('https://greengenerationinitiative.org/about/')

    with open(f'test.json', 'w') as f:
        json.dump(cwlr.get_state(), f)


def lassie_test():
    with open(f'test.json', 'w') as f:
        l = Lassie()
        l.request_opts = {
            'headers': {
                'Accept-Language': 'en-US,en'
            }
        }
        l.parser = "html.parser"

        lassie_res = l.fetch(
            'https://sproutsocial.com/insights/twitter-cards/')
        # 'https://greengenerationinitiative.org/about/'

        html = lassie_res['html']

        soup = BeautifulSoup(html, features="lxml")
        for s in soup(['script', 'style']):
            s.decompose()

        lassie_res['html'] = remove_stopwords(' '.join(soup.stripped_strings))

        json.dump(lassie_res, f)


def main():
    start_time = time.time()
    test_crawler()
    print("Elapsed time: %s seconds" % (time.time() - start_time))


if __name__ == '__main__':
    main()
