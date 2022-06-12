import json
from .constants import SECTIONS, CONFIG_FILE


def get_configuration_section(config, section) -> dict:
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

    if config is None:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)[section]

    return config.get(section, {})


def get_searching_config(config) -> tuple:
    """Gets the configuration parameters from the searching section

    Returns
    -------
    tuple
        All configuration parameters or their default in tuple form

    """
    searching_config = get_configuration_section(config, "searching")

    if "profiles" not in searching_config:
        raise KeyError("Necessary parameter <profiles> in searching section is not defined in configuration file.")

    profiles = searching_config["profiles"]

    if "keywords" not in searching_config and "hashtags" not in searching_config:
        raise KeyError(
            "Necessary parameters <keywords> and <hashtags> in searching section are not defined in configuration "
            "file. At least one must be defined.")

    keywords = searching_config.get("keywords", [])
    hashtags = searching_config.get("hashtags", [])
    exclude = searching_config.get("exclude", [])
    countries = searching_config.get("countries", [])
    languages = searching_config.get("languages", ["en"])
    start_time = searching_config.get("start_time")
    end_time = searching_config.get("end_time")

    if len(start_time) == 0:
        start_time = None

    if len(end_time) == 0:
        end_time = None

    return profiles, keywords, hashtags, exclude, countries, languages, start_time, end_time


def get_discovery_config(config) -> tuple:
    """Gets the configuration parameters from the discovery section

    Returns
    -------
    tuple
        All configuration parameters

    """
    discovery_config = get_configuration_section(config, "discovery")

    if "keywords" not in discovery_config:
        raise KeyError("Necessary parameter <keywords> in discovery section is not defined in configuration file.")

    if "tweets_per_profile" not in discovery_config:
        raise KeyError(
            "Necessary parameter <tweets_per_profile> in discovery section is not defined in configuration file.")

    keywords = discovery_config["keywords"]
    tweets_per_profile = discovery_config["tweets_per_profile"]

    return keywords, tweets_per_profile


def get_extraction_config(config) -> tuple:
    """Gets the configuration parameters from the extraction section

    Returns
    -------
    dict
        The selected extraction parameters

    """
    extraction_config = get_configuration_section(config, "extraction")

    if "links_per_profile" not in extraction_config:
        raise KeyError(
            "Necessary parameter <links_per_profile> in extraction section is not defined in configuration file.")

    links_per_profile = extraction_config.get("links_per_profile")

    entities_config = {}

    for key, value in extraction_config.get("entities", {}).items():
        if bool(value):
            entities_config[key] = True

    return links_per_profile, entities_config
