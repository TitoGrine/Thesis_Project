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


def process_profile_links(profile_info, links_per_user, entities_params):
    username = profile_info.get('username')
    name = process_twitter_name(profile_info.get('name'))

    links = profile_info.get('links')

    print(f"\033[92m Profile {username} collected {len(links)} links. \033[0m")

    links_info, remaining_links = crawl_links(links, links_per_user, entities_params, (username, name))

    profile_info.pop('links')
    profile_info['processed_links'] = links_info
    profile_info['unprocessed_links'] = remaining_links

    return profile_info
