import os.path
import shutil

from itertools import repeat
from multiprocessing import get_context

from .crawl import crawl_links
from src.utils import get_configuration_section, process_twitter_name, OUTPUT_DIR, PROFILE_INFO_FILE, ES_INDEX

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


def delete_profile_temp_dir(profile_identifier):
    profile_dir = f"{OUTPUT_DIR}/{profile_identifier}"

    if os.path.exists(profile_dir):
        shutil.rmtree(profile_dir, True)


def process_profile_links(profile, extraction_params):
    profile_file = f"{OUTPUT_DIR}/{profile}/{PROFILE_INFO_FILE}"

    if not os.path.exists(profile_file):
        print(f"Path {profile_file} doesn't exist.", flush=True)
        return

    file_mode = "r" if ".json" in PROFILE_INFO_FILE else "rb"

    with open(profile_file, file_mode) as f:
        profile_info = serializer.load(f)

    if profile_info is None:
        delete_profile_temp_dir(profile)
        return

    username = profile_info.get('username')
    name = process_twitter_name(profile_info.get('name'))

    links = profile_info.get('links')

    if links is None:
        delete_profile_temp_dir(profile)
        return

    links_info = crawl_links(links, extraction_params, (username, name))

    # if len(links_info) == 0:
    #     delete_profile_temp_dir(profile)

    profile_info['links'] = links_info

    # file_mode = file_mode.replace("r", "w")

    # with open(profile_file, file_mode) as f:
    #     serializer.dump(profile_info, f)
    return profile_info


def process_profiles(profile_identifiers):
    extraction_params = get_extraction_config()

    with get_context().Pool() as pool:
        results = pool.starmap(process_profile_links, zip(profile_identifiers, repeat(extraction_params)))

        # while True:
        #     if all([result.ready() for result in results]):
        #         print(f"Error results: {len([result.get() for result in results if not result.successful()])}")
        #         break

    return results
