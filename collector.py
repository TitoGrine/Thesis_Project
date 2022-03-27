import os
import re
import sys
import json
import nltk
import numpy
import tweepy
import pickle
import logging

from pprint import pprint
from bloom_filter2 import BloomFilter
from gensim.corpora import Dictionary
from gensim.test.utils import datapath
from gensim.parsing import preprocessing
from nltk.tokenize import RegexpTokenizer
from gensim.models import LdaModel, HdpModel, EnsembleLda
from nltk.stem.wordnet import WordNetLemmatizer

nltk.download('wordnet')
nltk.download('omw-1.4')

if False:
    logging.basicConfig(
        format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


def remove_urls(tweet): return re.sub(
    r'(https?:\/\/)(\s)*(www\.)?(\s)*((\w|\s)+\.)*([\w\-\s]+\/)*([\w\-]+)((\?)?[\w\s]*=\s*[\w\%&]*)*', "", tweet, flags=re.MULTILINE)


def remove_mentions(tweet): return re.sub(
    r'@\w+', "", tweet, flags=re.MULTILINE)


def remove_retweet_tag(tweet): return re.sub(
    r'(^|\b)RT\b', "", tweet, flags=re.MULTILINE)


def remove_sanitized_chars(tweet): return re.sub(
    r'&\w+', "", tweet, flags=re.MULTILINE)


def remove_short(tweet): return preprocessing.strip_short(tweet, minsize=3)


class Collector:
    # MAX_TWEETS = 100
    MAX_TWEETS = 7500
    # Set training parameters.
    CHUNKSIZE = 1000
    PASSES = 20
    ITERATIONS = 400
    EVAL_EVERY = None  # Don't evaluate model perplexity, takes too much time.

    api = tweepy.Client(
        bearer_token='AAAAAAAAAAAAAAAAAAAAADTxXwEAAAAApg4qeQrET9wiXNc8VqrxZF9aK%2Bs%3DT04MJA4P6nj14b41JzTfivhlWICAtQhmzO6XxvQipxISmh5pcS')

    user_fields = ["description", "entities", "location", "name"]

    tweet_fields = ["text", "author_id", "context_annotations",
                    "entities", "lang", "referenced_tweets"]

    def __init__(self, handle, user=None, data_folder="data"):
        self.handle = handle
        self.data_folder = data_folder
        self.user_folder = f'{data_folder}/{handle}'

        self.urls_bf = BloomFilter()
        # self.entities_bf = BloomFilter()

        if not os.path.exists(self.user_folder):
            os.makedirs(self.user_folder)
            os.makedirs(f"{self.user_folder}/models")

        if user is None:
            self.force_init(handle, data_folder)
        else:
            self.id = user.id
            self.name = user.name
            self.location = user.location
            self.description = self.process_text(user.description)
            self.extract_profile_urls(user.entities)

    def force_init(self, handle, data_folder):
        try:
            user = self.api.get_user(
                username=handle, user_fields=self.user_fields)

            self.id = user.data.id
            self.name = user.data.name
            self.location = user.data.location
            self.description = self.process_text(user.data.description)
            self.extract_profile_urls(user.data.entities)
        except Exception as e:
            print(f"Error initializing: {e}")
            self.id = None

    def valid_tweet(self, tweet):
        return 'lang' not in tweet or ('lang' in tweet and tweet['lang'] == "en")

    def process_text(self, text):
        return preprocessing.preprocess_string(text, filters=[
            remove_urls, remove_sanitized_chars, remove_retweet_tag, remove_mentions, str.lower, preprocessing.strip_tags, preprocessing.strip_punctuation, preprocessing.strip_numeric, preprocessing.strip_non_alphanum, preprocessing.strip_multiple_whitespaces, preprocessing.remove_stopwords, preprocessing.strip_short])

    def extract_profile_urls(self, entities):
        if entities is None:
            return

        urls = []

        if 'url' in entities and 'urls' in entities['url']:
            explicit_urls = entities['url']['urls']
            for url in explicit_urls:
                if url['expanded_url'] not in self.urls_bf:
                    urls.append(url['expanded_url'])
                    self.urls_bf.add(url['expanded_url'])

        if "description" in entities and 'urls' in entities['description']:
            description_urls = entities['description']['urls']
            for url in description_urls:
                if url['expanded_url'] not in self.urls_bf:
                    urls.append(url['expanded_url'])
                    self.urls_bf.add(url['expanded_url'])

        with open(f'{self.user_folder}/urls.txt', 'a+', encoding='UTF8') as f:
            self.write_to_file(f, '\n'.join(urls))

    def extract_tweet_urls(self, tweet):
        if not 'entities' in tweet:
            return []

        entities = tweet['entities']

        if not "urls" in entities:
            return []

        urls = []

        for url in entities['urls']:
            if url['expanded_url'] not in self.urls_bf:
                urls.append(url['expanded_url'])
                self.urls_bf.add(url['expanded_url'])

        return urls

    def extract_context_entities(self, tweet):
        if not 'context_annotations' in tweet:
            return []

        context = tweet['context_annotations']

        entities = []

        for annotation in context:
            entity = annotation['entity']['name']

            if entity not in self.entities_bf:
                entities.append(entity)
                self.entities_bf.add(entity)

        return entities

    def retweet_id(self, tweet):
        if 'referenced_tweets' not in tweet:
            return -1

        referenced_tweets = tweet['referenced_tweets']

        for referenced_tweet in referenced_tweets:
            if referenced_tweet['type'] == 'retweeted':
                return int(referenced_tweet['id'])

        return -1

    def parse_tweet(self, tweet, retweets):
        data = tweet.data

        if not self.valid_tweet(data):
            return None

        # in the future check what makes sense to treat differently when it is a retweet
        retweet_id = self.retweet_id(data)
        is_retweet = bool(retweet_id > 0)

        text = retweets[retweet_id] if is_retweet else data['text']

        return {
            'text': self.process_text(text),
            'urls': self.extract_tweet_urls(data) if not is_retweet else [],
            # 'entities': self.extract_context_entities(data),
            'retweet': is_retweet
        }

    def write_to_file(self, file, s, end="\n"):
        if len(s) > 0:
            file.write(s + end)

    def save_tweets(self, tweets, retweets):
        if tweets is None:
            return

        originals_file = open(f'{self.user_folder}/tweets.txt', 'a+')
        retweets_file = open(f'{self.user_folder}/retweets.txt', 'a+')
        urls_file = open(f'{self.user_folder}/urls.txt', 'a+')
        # entities_file = open(f'{self.user_folder}/entities.txt', 'a+')

        for tweet in tweets:
            parsed_tweet = self.parse_tweet(tweet, retweets)

            if parsed_tweet is None:
                continue

            text = ' '.join(parsed_tweet['text'])

            if bool(parsed_tweet['retweet']):
                self.write_to_file(retweets_file, text)
            else:
                self.write_to_file(originals_file, text)

                if len(parsed_tweet['urls']) > 0:
                    self.write_to_file(
                        urls_file, '\n'.join(parsed_tweet['urls']))

            # self.write_to_file(entities_file, ' '.join(
            #     parsed_tweet['entities']))

        originals_file.close()
        retweets_file.close()
        urls_file.close()
        # entities_file.close()

    def extract_tweets(self):
        tweet_count = 0
        next_token = None

        while tweet_count < self.MAX_TWEETS:
            res = self.api.get_users_tweets(
                id=self.id, max_results=100, tweet_fields=self.tweet_fields, pagination_token=next_token, expansions="referenced_tweets.id")

            retweets = {}

            if 'tweets' in res.includes:
                retweets = {
                    retweet.id: retweet.text for retweet in res.includes['tweets']}

            self.save_tweets(res.data, retweets)

            if 'next_token' not in res.meta:
                return

            tweet_count += res.meta['result_count']
            next_token = res.meta['next_token']

    def load_tweets(self, word_file):
        if not os.path.exists(word_file):
            return None

        with open(word_file, 'r', encoding='UTF8') as f:
            return f.readlines()

    def merge_docs(self, docs, n):
        for i in range(0, len(docs), n):
            yield preprocessing.strip_short(" ".join(docs[i:i + n]).replace('\n', ''))

    def get_topics(self, word_file, model_file):
        docs = self.load_tweets(word_file)

        if len(docs) == 0:
            return []

        tokenizer = RegexpTokenizer(r'\w+')
        lemmatizer = WordNetLemmatizer()

        docs = list(self.merge_docs(docs, 10))

        for idx in range(len(docs)):
            docs[idx] = tokenizer.tokenize(docs[idx])

        docs = [[lemmatizer.lemmatize(token) for token in doc] for doc in docs]

        dictionary = Dictionary(docs)
        dictionary.filter_extremes(no_below=0.1, no_above=0.99)

        if len(dictionary) < 10:
            return []

        corpus = [dictionary.doc2bow(doc) for doc in docs]

        num_tokens = len(dictionary)
        num_documents = len(corpus)

        temp = dictionary[0]
        id2word = dictionary.id2token

        stable_model = None
        attempts = 0

        while stable_model is None and attempts < 10:
            model = EnsembleLda(
                corpus=corpus,
                id2word=id2word,
                num_topics=10
            )

            stable_model = model.generate_gensim_representation()
            attempts += 1

        if stable_model is None:
            print(f"Unable to extract stable topics.")
            return []

        top_topics = stable_model.top_topics(corpus, topn=10)[:5]

        return [[topic_word for topic_value, topic_word in topic_distribution]
                for topic_distribution, coherence in top_topics]

    def get_topical_words(self):
        tweets_topics = self.get_topics(
            f'{self.user_folder}/tweets.txt', f'{self.user_folder}/models/tweet_model')

        retweets_topics = self.get_topics(
            f'{self.user_folder}/retweets.txt', f'{self.user_folder}/models/retweet_model')

        topical_words_state = {
            "description": self.description,
            "tweets": tweets_topics,
            "retweets": retweets_topics
        }

        with open(f'test.json', 'w') as f:
            json.dump(topical_words_state, f)

        # with open(f'{self.user_folder}/topical_words.pickle', 'ab+') as f:
        #     pickle.dump(topical_words_state, f)
