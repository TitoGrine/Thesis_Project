import json
from lassie import Lassie
from bs4 import BeautifulSoup
from gensim.parsing.preprocessing import remove_stopwords
from crawler import Crawler


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
            'http://www.youtube.com/watch?v=dQw4w9WgXcQ')
        # 'https://greengenerationinitiative.org/about/'

        html = lassie_res['html']

        soup = BeautifulSoup(html, features="lxml")
        for s in soup(['script', 'style']):
            s.decompose()

        lassie_res['html'] = remove_stopwords(' '.join(soup.stripped_strings))

        json.dump(lassie_res, f)


def main():
    test_crawler()


if __name__ == '__main__':
    main()
