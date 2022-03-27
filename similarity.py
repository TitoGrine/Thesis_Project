import gensim.downloader as downloader
import pickle
import numpy
import math


class Scorer:
    def __init__(self, model_name="glove-wiki-gigaword-300"):
        self.embed_model = downloader.load(model_name)

    def calc_words_embed(self, words):
        embed_array = []

        for word in words:
            try:
                embed_array.append(self.embed_model.get_vector(word))

            except KeyError:
                continue

        return embed_array

    def get_keywords_embed(self, keywords):
        vectorized_keywords = []

        for keyword in keywords:
            try:
                vectorized_keywords.append(
                    self.embed_model.get_vector(keyword))
            except KeyError:
                continue

        if len(vectorized_keywords) == 0:
            return []

        return sum(vectorized_keywords)

    def calc_similarity_score(self, keywords_embed, words_embed):
        similarities = []

        if len(words_embed) == 0:
            return -1

        for keyword_embed in keywords_embed:
            best_similarity = -1
            for word_embed in words_embed:
                if len(word_embed) > 0:
                    res = numpy.sort(
                        self.embed_model.cosine_similarities(keyword_embed, word_embed))

                    # Consider only the top four most similar topic words
                    best_similarity = max(
                        best_similarity, numpy.average(res[-4:]))

            similarities.append(best_similarity)

        similarities = numpy.sort(similarities)

        # Discard the bottom 30% scoring keywords
        discard_index = math.floor(len(similarities) * 0.3)

        return numpy.average(similarities[discard_index:])

    def get_similarity_scores(self, keywords_array, user_dir):
        keywords_embed = [self.get_keywords_embed(
            keywords) for keywords in keywords_array if len(keywords) > 0]

        keywords_embed = [
            keyword_embed for keyword_embed in keywords_embed if len(keyword_embed) > 0]

        if len(keywords_embed) == 0:
            return

        with open(f'{user_dir}/topical_words.pickle', 'rb') as f:
            topical_words_state = pickle.load(f)

            description_words = [self.calc_words_embed(
                topical_words_state["description"])]
            tweets_topics = [embed for embed in [self.calc_words_embed(
                words) for words in topical_words_state["tweets"]] if len(embed) > 0]
            retweets_topics = [embed for embed in [self.calc_words_embed(
                words) for words in topical_words_state["retweets"]] if len(embed) > 0]

            # print(
            #     f"Description similarity score is {self.calc_similarity_score(keywords_embed, description_words)}")
            # print(
            #     f"Tweet similarity score is {self.calc_similarity_score(keywords_embed, tweets_topics)}")
            # print(
            #     f"Retweet similarity score is {self.calc_similarity_score(keywords_embed, retweets_topics)}")

            return [self.calc_similarity_score(keywords_embed, description_words), self.calc_similarity_score(keywords_embed, tweets_topics), self.calc_similarity_score(keywords_embed, retweets_topics)]
