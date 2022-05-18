import json
from .constants import SECTIONS, CONFIG_FILE


def get_configuration_section(section) -> dict:
    """Gets the configuration dict for a given section of the configuration file

    Parameters
    ----------
    section : str
        Section to retrieve from configuration file

    Returns
    -------
    dict
        Dictionary object with the configurations for the given section
    """
    if section not in SECTIONS:
        raise KeyError(f"Configuration file does not have {section} as a section.")

    with open(CONFIG_FILE, "r") as f:
        return json.load(f)[section]


def get_searching_config() -> tuple:
    """Gets the configuration parameters from the searching section

    Returns
    -------
    tuple
        All configuration parameters or their default in tuple form

    """
    searching_config = get_configuration_section("searching")

    if "users" not in searching_config:
        raise KeyError("Necessary parameter <users> in searching section is not defined in configuration file.")

    users = searching_config["users"]

    if "keywords" not in searching_config and "hashtags" not in searching_config:
        raise KeyError(
            "Necessary parameters <keywords> and <hashtags> in searching section are not defined in configuration "
            "file. At least one must be defined.")

    keywords = searching_config.get("keywords") or []
    hashtags = searching_config.get("hashtags") or []
    exclude = searching_config.get("_exclude_") or []
    countries = searching_config.get("_countries_") or []
    languages = searching_config.get("_languages_") or ["en"]
    start_time = searching_config.get("_start_time_") or None
    end_time = searching_config.get("_end_time_") or None

    return users, keywords, hashtags, exclude, countries, languages, start_time, end_time


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


def get_extraction_config() -> dict:
    """Gets the configuration parameters from the extraction section

    Returns
    -------
    dict
        The selected extraction parameters

    """
    extraction_config = get_configuration_section("extraction")

    for key, value in extraction_config.items():
        if not value:
            del extraction_config[key]

    return extraction_config
