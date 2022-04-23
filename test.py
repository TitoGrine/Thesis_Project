import os
import csv
import sys
import time
import math
import numpy
import tweepy

from extractor import Extractor
from similarity import Scorer
from multiprocessing import Pool
from gensim.parsing import preprocessing

api = tweepy.Client(
    bearer_token='AAAAAAAAAAAAAAAAAAAAADTxXwEAAAAApg4qeQrET9wiXNc8VqrxZF9aK%2Bs%3DT04MJA4P6nj14b41JzTfivhlWICAtQhmzO6XxvQipxISmh5pcS')

user_fields = ["description", "entities", "location", "name"]


themes_dict = {
    "ambient_music": [["ambient", "music"], ["ambient", "techno"], ["ambient", "house"], ["biomusic"], ["chill-out"], ["atmospheric"], ["downtempo"], ["nature", "soundscapes"], ["electronic"]],
    "climate_activist": [['climate', 'change'], ['climate', 'activism'], ['climate', 'movement'], ['environmental', 'movement'], ['green', 'future'], ["climate", "justice"], ['protesting'], ['save', 'planet'], ["environment"], ['paris', 'agreement']],
    "quantum_information": [["quantum", "information"], ["quantum", "system"], ["quantum", "theory"], ["computer", "science"], ["quantum", "mechanics"], ["cryptography"], ["quantum", "information", "processing"], ["qubits"], ["quantum", "computing"]],
    "contemporary_artists": [["contemporary", "art"], ["mixed", "medium"], ["painting"], ["modernism"], ["impressionism"], ["art", "gallery"], ["art", "museum"], ["art", "piece"], ["avant-garde"], ["art", "collector"], ["painting"], ["abstract", "painting"], ["minimalism"], ["new", "media"]],
    "tennis_players": [["tennis", "player"], ["tennis"], ["racket"], ["sport"], ["tennis", "court"], ["grand", "slam"], ["tennis", "tournament"], ["ATP"], ["australian", "open"], ["us", "open"], ["rolland", "garros"], ["wimbledon"]],
    "information_retrieval": [["information", "retrieval"], ["information", "system"], ["information", "science"], ["computing"], ["document", "searching"], ["metadata"], ["web", "search"], ["data", "extraction"]],
}


def extract_user_tweets_and_topics(twitter_handle, user):
    coll = Extractor(twitter_handle, user)
    coll.extract_tweets()
    # coll.get_topical_words()
    print(f"Extracted tweets from {twitter_handle}.")


def batch_request_users(twitter_handles):
    users = api.get_users(usernames=twitter_handles,
                          user_fields=user_fields).data

    for user in users:
        if not os.path.exists(f"data/{user['username']}/topical_words.pickle"):
            try:
                extract_user_tweets_and_topics(user['username'], user)
            except Exception as e:
                print(f"Error processing {twitter_handle}: {e}")
                return


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def extract_all_tweets():
    with open("sources/themes_dataset.csv", 'r', encoding='UTF8') as f:
        reader = csv.reader(f)
        next(reader)

        handles = []

        for [theme, handle] in reader:
            handles.append(handle)

        handles_chunks = list(chunks(handles, 100))

        pool = Pool(6)

        for chunk in handles_chunks:
            pool.apply_async(batch_request_users, (chunk,))

        pool.close()
        pool.join()


def get_user_tweets_and_topics(twitter_handle, user=None):
    try:
        coll = Extractor(twitter_handle, user)
        coll.extract_tweets()
        coll.get_topical_words()
        print(f"Extracted topics from {twitter_handle}")
    except Exception as e:
        print(f"Error processing {twitter_handle}: {e}")
        return


def batch_request(twitter_handles):
    users = api.get_users(usernames=twitter_handles,
                          user_fields=user_fields).data

    for user in users:
        if not os.path.exists(f"data/{user['username']}/topical_words.pickle"):
            get_user_tweets_and_topics(user['username'], user)


def extract_all_topics():
    with open("sources/themes_dataset.csv", 'r', encoding='UTF8') as f:
        reader = csv.reader(f)
        next(reader)

        handles = []

        for [theme, handle] in reader:
            handles.append(handle)

        handles_chunks = list(chunks(handles, 100))

        for chunk in handles_chunks:
            batch_request(chunk)


def get_user_similarity(theme, twitter_handle):
    scorer = Scorer("glove-twitter-25")

    scorer.get_similarity_scores(themes_dict[theme], f"data/{twitter_handle}")


def get_wrong_theme(right_theme, index):
    parsed_keys = [key for key in themes_dict.keys() if key != right_theme]

    return themes_dict[parsed_keys[index % len(parsed_keys)]]


def get_positive_similarities(rows, ft_wiki_scorer, glove_twitter_scorer, glove_wiki_scorer, w2v_news_scorer):
    with open("sources/positive_similarities_dataset.csv", 'w', encoding='UTF8') as f:
        writer = csv.writer(f)
        header = ['theme', 'twitter_handle', 'description_ft_wiki', 'tweets_ft_wiki', 'retweets_ft_wiki', 'description_glove_twitter', 'tweets_glove_twitter',
                  'retweets_glove_twitter', 'description_glove_wiki', 'tweets_glove_wiki', 'retweets_glove_wiki', 'description_w2v_news', 'tweets_w2v_news', 'retweets_w2v_news']
        writer.writerow(header)

        index = 0

        for [theme, handle] in rows:

            index += 1

            try:
                ft_wiki_similarities = ft_wiki_scorer.get_similarity_scores(
                    themes_dict[theme], f"data/{handle}")
                glove_twitter_similarities = glove_twitter_scorer.get_similarity_scores(
                    themes_dict[theme], f"data/{handle}")
                glove_wiki_similarities = glove_wiki_scorer.get_similarity_scores(
                    themes_dict[theme], f"data/{handle}")
                w2v_news_similarities = w2v_news_scorer.get_similarity_scores(
                    themes_dict[theme], f"data/{handle}")

                row = numpy.concatenate(([theme, handle], ft_wiki_similarities,
                                         glove_twitter_similarities, glove_wiki_similarities, w2v_news_similarities))

                writer.writerow(row)
            except:
                print("Error column")
                writer.writerow([theme, handle, -1, -1, -1, -
                                1, -1, -1, -1, -1, -1, -1, -1, -1])


def get_negative_similarities(rows, ft_wiki_scorer, glove_twitter_scorer, glove_wiki_scorer, w2v_news_scorer):
    with open("sources/negative_similarities_dataset.csv", 'w', encoding='UTF8') as f:
        writer = csv.writer(f)
        header = ['theme', 'twitter_handle', 'description_ft_wiki', 'tweets_ft_wiki', 'retweets_ft_wiki', 'description_glove_twitter', 'tweets_glove_twitter',
                  'retweets_glove_twitter', 'description_glove_wiki', 'tweets_glove_wiki', 'retweets_glove_wiki', 'description_w2v_news', 'tweets_w2v_news', 'retweets_w2v_news']
        writer.writerow(header)

        index = 0

        for [theme, handle] in rows:
            index += 1

            try:
                ft_wiki_similarities = ft_wiki_scorer.get_similarity_scores(
                    get_wrong_theme(theme, index), f"data/{handle}")
                glove_twitter_similarities = glove_twitter_scorer.get_similarity_scores(
                    get_wrong_theme(theme, index), f"data/{handle}")
                glove_wiki_similarities = glove_wiki_scorer.get_similarity_scores(
                    get_wrong_theme(theme, index), f"data/{handle}")
                w2v_news_similarities = w2v_news_scorer.get_similarity_scores(
                    get_wrong_theme(theme, index), f"data/{handle}")

                row = numpy.concatenate(([theme, handle], ft_wiki_similarities,
                                         glove_twitter_similarities, glove_wiki_similarities, w2v_news_similarities))

                writer.writerow(row)
            except:
                print("Error column")
                writer.writerow([theme, handle, -1, -1, -1, -
                                1, -1, -1, -1, -1, -1, -1, -1, -1])


def get_similarities_test(rows):
    ft_wiki_scorer = Scorer("word2vec-google-news-300")

    with open("sources/positive_similarities_dataset_test.csv", 'a', encoding='UTF8') as f:
        writer = csv.writer(f)
        header = ['theme', 'twitter_handle', 'description_ft_wiki',
                  'tweets_ft_wiki', 'retweets_ft_wiki']
        writer.writerow(header)

        for [theme, handle] in rows:
            try:
                ft_wiki_similarities = ft_wiki_scorer.get_similarity_scores(
                    themes_dict[theme], f"data/{handle}")

                row = numpy.concatenate(
                    ([theme, handle], ft_wiki_similarities))

                writer.writerow(row)
            except:
                writer.writerow([theme, handle, -1, -1, -1])


def save_similarities():
    ft_wiki_scorer = Scorer("fasttext-wiki-news-subwords-300")
    print("Loaded fasttext-wiki-news-subwords-300.")
    glove_twitter_scorer = Scorer("glove-twitter-200")
    print("Loaded glove-twitter-200.")
    glove_wiki_scorer = Scorer("glove-wiki-gigaword-300")
    print("Loaded glove-wiki-gigaword-300.")
    w2v_news_scorer = Scorer("word2vec-google-news-300")
    print("Loaded word2vec-google-news-300.", end="\n\n")

    with open("sources/themes_dataset.csv", 'r', encoding='UTF8') as f:
        reader = csv.reader(f)
        next(reader)

        get_positive_similarities(
            reader, ft_wiki_scorer, glove_twitter_scorer, glove_wiki_scorer, w2v_news_scorer)

    with open("sources/themes_dataset.csv", 'r', encoding='UTF8') as f:
        reader = csv.reader(f)
        next(reader)

        get_negative_similarities(
            reader, ft_wiki_scorer, glove_twitter_scorer, glove_wiki_scorer, w2v_news_scorer)


def main():
    # get_user_similarity('ambient_music', 'WilliamBasinski')
    # get_user_similarity('GretaThunberg')

    # extract_all_topics()

    start_time = time.time()
    get_user_tweets_and_topics('TheOmniLiberal')
    print("Elapsed time: %s seconds" % (time.time() - start_time))

    # save_similarities()


if __name__ == '__main__':
    main()
