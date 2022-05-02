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
