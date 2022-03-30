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

    cwlr.print_state()


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


def trafilatura_test():
    # downloaded = fetch_url('https://greengenerationinitiative.org/about/')
    # print(extract(downloaded))
    to_visit, known_urls = focused_crawler(
        'https://greengenerationinitiative.org/about/', max_seen_urls=50)

    print("Total Internal links:")
    pprint(list(to_visit))
    print("Total External links:")
    pprint(list(known_urls))


def main():
    test_crawler()


if __name__ == '__main__':
    main()
