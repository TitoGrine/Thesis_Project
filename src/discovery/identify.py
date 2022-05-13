from src.utils import get_configuration_section
from .analyze import analyze_profiles, batch_analyze_profiles, analyze_profile, batch_request_profiles
import gensim.downloader as downloader
from src.utils import chunks, flatten, WORD_MODEL
from .embedding import get_words_embedding


def get_discovery_config() -> tuple:
    """Gets the configuration parameters from the discovery section

    Returns
    -------
    tuple
        All configuration parameters

    """
    discovery_config = get_configuration_section("discovery")

    if "keywords" not in discovery_config:
        raise KeyError("Necessary parameter <keywords> in discovery section is not defined in configuration file.")

    if "tweets_per_user" not in discovery_config:
        raise KeyError(
            "Necessary parameter <tweets_per_user> in discovery section is not defined in configuration file.")

    keywords = discovery_config["keywords"]
    tweets_per_user = discovery_config["tweets_per_user"]

    return keywords, tweets_per_user


def identify_related_profiles(ids, spark_context) -> list[str]:
    keywords, tweets_per_user = get_discovery_config()

    word_model = downloader.load(WORD_MODEL)
    embedded_keywords = get_words_embedding(keywords, word_model)

    word_model_bv = spark_context.broadcast(word_model)

    id_chunks = list(chunks(ids, 100))

    profile_responses = flatten([batch_request_profiles(id_chunk) for id_chunk in id_chunks])

    rdd = spark_context.parallelize(profile_responses)

    analyzed_profiles = rdd.map(lambda pf: analyze_profile(pf, embedded_keywords, tweets_per_user, word_model_bv.value))

    related_profiles = analyzed_profiles.filter(lambda profile: profile is not None).collect()

    return related_profiles

    # return [potential_profile for potential_profile in analyze_profiles(ids, keywords, tweets_per_user) if
    #         potential_profile is not None]
