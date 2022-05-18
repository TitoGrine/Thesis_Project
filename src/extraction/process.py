import os.path
import shutil

from multiprocessing import get_context

from .crawl import crawl_links
from src.utils import process_twitter_name, OUTPUT_DIR, PROFILE_INFO_FILE
from .. import get_extraction_config

if ".json" in PROFILE_INFO_FILE:
    import json as serializer
else:
    import pickle as serializer


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

    if len(links_info) == 0:
        delete_profile_temp_dir(profile)

    profile_info['links'] = links_info

    file_mode = file_mode.replace("r", "w")

    with open(profile_file, file_mode) as f:
        serializer.dump(profile_info, f)

    return profile_info
