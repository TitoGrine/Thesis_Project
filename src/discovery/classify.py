import math

import nltk
import numpy

from gensim.corpora import Dictionary
from gensim.models import EnsembleLda
from nltk.tokenize import RegexpTokenizer
from nltk.stem.wordnet import WordNetLemmatizer

from .embedding import get_words_embedding
from src.utils import merge_docs

nltk.download('wordnet')
nltk.download('omw-1.4')


def get_topic_words(words):
    docs = list(merge_docs(words, 10))

    tokenizer = RegexpTokenizer(r'\w+')
    lemmatizer = WordNetLemmatizer()

    docs = [tokenizer.tokenize(doc) for doc in docs]
    docs = [[lemmatizer.lemmatize(token) for token in doc] for doc in docs]

    dictionary = Dictionary(docs)
    dictionary.filter_extremes(no_below=0.1, no_above=0.99)

    if len(dictionary) < 10:
        return []

    corpus = [dictionary.doc2bow(doc) for doc in docs]
    # Necessary to use the dictionary
    temp = dictionary[0]
    id2word = dictionary.id2token

    stable_model = None
    attempt_count = 0

    while stable_model is None and attempt_count < 10:
        model = EnsembleLda(corpus=corpus, id2word=id2word, num_topics=10)
        stable_model = model.generate_gensim_representation()

        attempt_count += 1

    if stable_model is None:
        return []

    top_topics = stable_model.top_topics(corpus, topn=10)[:5]

    return [[topic_word for topic_value, topic_word in topic_distribution]
            for topic_distribution, coherence in top_topics]


def calculate_similarity_score(keywords_embedding, words_embedding, word_model):
    if len(keywords_embedding) or len(words_embedding) == 0:
        return -1

    similarity_scores = []

    for keyword_embedding in keywords_embedding:
        best_similarity = -1

        for word_embedding in words_embedding:
            if len(word_embedding) <= 0:
                continue

            similarities = numpy.sort(word_model.cosine_similarities(keyword_embedding, word_embedding))
            # Consider only the top 4 most similar topic words
            best_similarity = max(best_similarity, numpy.average(similarities))

        similarity_scores.append(best_similarity)

    similarity_scores = numpy.sort(similarity_scores)
    # Discard the bottom ~30% of scoring keywords
    discard_index = math.floor(len(similarity_scores) * 0.3)

    return numpy.average(similarity_scores[discard_index:])


def calculate_profile_score(keywords, word_model, description, tweets, retweets):
    tweets_topic_words = get_topic_words(tweets)
    retweets_topic_words = get_topic_words(retweets)

    description_score = calculate_similarity_score(keywords, [get_words_embedding(description, word_model)], word_model)
    tweets_score = calculate_similarity_score(keywords,
                                              [get_words_embedding(words, word_model) for words in tweets_topic_words],
                                              word_model)
    retweets_score = calculate_similarity_score(keywords, [get_words_embedding(words, word_model) for words in
                                                           retweets_topic_words], word_model)

    return numpy.average([description_score, tweets_score, retweets_score])