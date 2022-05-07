import os.path

from multiprocessing import get_context

from .crawl import crawl_links
from src.utils import get_configuration_section, process_twitter_name, OUTPUT_DIR, PROFILE_INFO_FILE

if ".json" in PROFILE_INFO_FILE:
    import json as serializer
else:
    import pickle as serializer


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


def process_profile_links(profile, extraction_params):
    profile_file = f"{OUTPUT_DIR}/{profile}/{PROFILE_INFO_FILE}"

    if not os.path.exists(profile_file):
        print(f"Path {profile_file} doesn't exist.", flush=True)
        return

    print(f"Processing profile {profile}", flush=True)
    file_mode = "r+" if ".json" in PROFILE_INFO_FILE else "r+b"

    with open(profile_file, file_mode) as f:
        profile_info = serializer.load(f)

        username = profile_info.get('username')
        name = process_twitter_name(profile_info.get('name'))

        links = profile_info.get('links')

        if links is None:
            print("No links")
            return

        links_info = crawl_links(links, extraction_params, (username, name))

        from pprint import pprint
        pprint(links_info)

        profile_info['links'] = links_info

        f.truncate()

        serializer.dump(profile_info, f)


def process_profiles(profile_identifiers):
    extraction_params = get_extraction_config()

    with get_context().Pool() as pool:
        for profile_identifier in profile_identifiers:
            pool.apply(process_profile_links, (profile_identifier, extraction_params))
