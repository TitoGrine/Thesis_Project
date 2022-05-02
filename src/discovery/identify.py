from src.utils import get_configuration_section


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


def identify_related_profiles(ids) -> set[str]:
    keywords, tweets_per_user = get_discovery_config()