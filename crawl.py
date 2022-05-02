import csv
import json
import os
import random
import time
from multiprocessing import get_context
from urllib.parse import urlparse

import numpy
import tweepy
from decouple import config

from crawler.crawler import Crawler
from src.utils import process_twitter_name

api = tweepy.Client(bearer_token=config('TWITTER_BEARER_TOKEN'))


def test_crawler(handle, url):
    domain_name = urlparse(url).netloc
    filename = f"websites/{handle}_{domain_name}"

    if os.path.exists(f"{filename}.json"):
        with open(f'{filename}.json', 'r') as f:
            state = json.load(f)

            if len(state["internal_links"]) > 1 or state["is_link_tree"]:
                return
            else:
                try:
                    cwlr = Crawler(crawl_javascript=True)
                    cwlr.crawl(url)
                    cwlr.save_state(filename)
                    print(f" · Finished recrawling {url} ·")
                except Exception as e:
                    print(f"Issue crawling {url}: {e}")
    else:
        try:
            cwlr = Crawler(crawl_javascript=False)
            cwlr.crawl(url)
            cwlr.save_state(filename)
            print(f" · Finished crawling {url} ·")
        except Exception as e:
            print(f"Issue crawling {url}: {e}")


def test_matching(handle, url):
    domain_name = urlparse(url).netloc
    filename = f"websites/{handle}_{domain_name}"

    if not os.path.exists(f"{filename}.json"):
        return

    with open(f'handle_mapping.json', 'r') as f:
        mapping = json.load(f)

        terms = [handle, mapping[handle]]

        print(f"Initial terms: {terms}.")

        cwlr = Crawler(state_file=filename)
        print(cwlr.check_for_matches(terms))
        # except Exception as e:
        #     print(f"Issue matching {url}: {e}")


def test_entity_extraction(handle, url):
    domain_name = urlparse(url).netloc
    filename = f"websites/{handle}_{domain_name}"

    if not os.path.exists(f"{filename}.json"):
        return

    cwlr = Crawler(state_file=filename)
    cwlr.extract_entitites()
    # except Exception as e:
    #     print(f"Issue matching {url}: {e}")


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def get_positive_matches(mapping, rows):
    with open("results/positive_matches_dataset.csv", 'w', encoding='UTF8') as f:
        writer = csv.writer(f)
        header = ['website', 'twitter_handle',
                  'twitter_username', "handle_score", "username_score"]
        writer.writerow(header)

        index = 0

        for [handle, website] in rows:

            index += 1
            username = mapping[handle]

            try:
                domain_name = urlparse(website).netloc
                filename = f"websites/{handle}_{domain_name}"

                cwlr = Crawler(state_file=filename)

                scores = cwlr.check_for_matches([handle, username])

                row = numpy.concatenate(([website, handle, username], scores))

                writer.writerow(row)
            except Exception as e:
                print(f"Error: {e}")
                writer.writerow([website, handle, username, -1, -1])


def get_negative_matches(mapping, rows):
    with open("results/negative_matches_dataset.csv", 'w', encoding='UTF8') as f:
        writer = csv.writer(f)
        header = ['website', 'twitter_handle',
                  'twitter_username', "handle_score", "username_score"]
        writer.writerow(header)

        usernames = list(mapping.keys())
        random.seed(42)

        index = 0

        for [handle, website] in rows:

            index += 1

            random_handle = handle

            while random_handle == handle:
                random_handle = usernames[(index + random.randint(0, 10)) % len(usernames)]

            random_username = mapping[random_handle]

            try:
                domain_name = urlparse(website).netloc
                filename = f"websites/{handle}_{domain_name}"

                cwlr = Crawler(state_file=filename)

                scores = cwlr.check_for_matches(
                    [random_handle, random_username])

                row = numpy.concatenate(
                    ([website, random_handle, random_username], scores))

                writer.writerow(row)
            except Exception as e:
                print(f"Error: {e}")
                writer.writerow(
                    [website, random_handle, random_username, -1, -1])


def save_matches():
    with open(f'handle_mapping.json', 'r') as f:
        mapping = json.load(f)

    with open("sources/websites_dataset.csv", 'r', encoding='UTF8') as f:
        reader = csv.reader(f)
        next(reader)
        get_positive_matches(mapping, reader)

    with open("sources/websites_dataset.csv", 'r', encoding='UTF8') as f:
        reader = csv.reader(f)
        next(reader)
        get_negative_matches(mapping, reader)


def batch_request(twitter_handles):
    users = api.get_users(usernames=twitter_handles).data

    res = {}

    for user in users:
        res[user['username']] = process_twitter_name(user["name"])

    return res


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

    # # save_websites()
    # test_crawler(
    #     "../test", "http://www.billhersh.info")
    # test_matching("steve_timeroom", "https://www.steveroach.bandcamp.com")
    test_entity_extraction("algore", "http://algore.com/")
    # save_matches()

    # print(unquote("https://www.steveroach.bandcamp.com"))

    print("Elapsed time: %s seconds" % (time.time() - start_time))


if __name__ == '__main__':
    main()
