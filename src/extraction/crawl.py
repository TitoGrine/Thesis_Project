import json
import time
import requests
import validators

from bs4 import BeautifulSoup
from bloom_filter2 import BloomFilter
from urllib.parse import urlparse, urljoin, unquote

from .extract import extract_link_entities
from .classify import calculate_link_profile_relatedness
from src.utils import standardize_url, link_from_host, clean_html, get_driver, url_is_downloadable, FAKE_USER_AGENT, \
    filter_meta_data, filter_amp_data, SESSION_TIMEOUT, CERTIFICATE_VERIFY, WEBSITE_RELATEDNESS_THRESHOLD, \
    MAX_CRAWL_DEPTH, SPECIAL_CRAWLING, normalize_unicode_text, REJECT_TYPES, remove_url_query, print_elapsed_time, \
    url_is_dowloadable_partial_check


def get_website_content(url, enable_javascript):
    driver = None

    if url_is_dowloadable_partial_check(url):
        return None, 418

    try:
        if enable_javascript:
            head_req = requests.request("HEAD", url, headers={
                'Accept-Language': 'en-US,en',
                'User-Agent': FAKE_USER_AGENT
            }, timeout=SESSION_TIMEOUT, verify=CERTIFICATE_VERIFY)
            status_code = head_req.status_code

            if url_is_downloadable(head_req.headers):
                return None, 418

            # Sometimes HEAD request returns 4** error when GET returns 200
            if 400 <= status_code < 500:
                head_req = requests.request("GET", url, headers={
                    'Accept-Language': 'en-US,en',
                    'User-Agent': FAKE_USER_AGENT
                }, timeout=SESSION_TIMEOUT, verify=CERTIFICATE_VERIFY)
                status_code = head_req.status_code

            if 400 <= status_code < 500:
                return None, status_code

            if url_is_downloadable(head_req.headers):
                return None, 418

            driver = get_driver()
            driver.get(url)
            source = driver.page_source

            driver.quit()
        else:
            response = requests.request("GET", url, headers={
                'Accept-Language': 'en-US,en'
            }, timeout=SESSION_TIMEOUT, verify=CERTIFICATE_VERIFY)
            status_code = response.status_code
            source = response.text

            if url_is_downloadable(response.headers):
                return None, 418

            if status_code == 403 or status_code == 406:
                response = requests.request("GET", url, headers={
                    'Accept-Language': 'en-US,en',
                    'User-Agent': FAKE_USER_AGENT
                }, timeout=SESSION_TIMEOUT, verify=CERTIFICATE_VERIFY)
                status_code = response.status_code
                source = response.text

    except:
        if enable_javascript and driver:
            driver.quit()

        return None, 404

    return source, status_code


def extract_link_tree_links(hostname, soup):
    if "linktr.ee" in hostname:
        script_contents = soup.find(id="__NEXT_DATA__").contents

        try:
            return [link["url"] for link in json.loads(script_contents[0])[
                "props"]["pageProps"]["account"]["links"] if "url" in link]
        except:
            return []
    elif "lnk.to" in hostname or "ampl.ink" in hostname:
        return [tag.attrs.get("href") for tag in soup.find_all(["a"])]
    elif "linkgenie.co" in hostname:
        linkgenie_links = [tag.attrs.get("href")
                           for tag in soup.find_all(["a"])]

        return [requests.get(link).url for link in linkgenie_links]
    elif "allmylinks.com" in hostname:
        return [tag.attrs.get("title") for tag in soup.find_all(["a"])]
    elif "biglink.to" in hostname or "withkoji.com" in hostname:
        return []


def extract_website_links(hostname, soup, link_info):
    if hostname in SPECIAL_CRAWLING:
        link_info['is_link_tree'] = True
        links = extract_link_tree_links(hostname, soup)
    else:
        links = [tag.attrs.get("href") for tag in soup.find_all(["a"])]

    return [unquote(link).strip() for link in links if link is not None]


def save_extracted_data(link_info, name, titles, keywords, description, images, soup, images_bf):
    if name and len(name) > 0 and name not in link_info['name']:
        link_info['name'].append(name)

    for title in titles:
        if title and len(title) > 0 and title not in link_info['title']:
            link_info['title'].append(title)

    for keyword in keywords:
        if keyword and len(keyword) > 0 and keyword not in link_info['keywords']:
            link_info['keywords'].append(keyword)

    if description and len(description) > 0:
        link_info['description'] += " " + normalize_unicode_text(description)

    if images and len(images) > 0:
        for image in images:
            image_url = remove_url_query(image.get('src'))

            if ("type" not in image or image["type"] not in REJECT_TYPES) and image_url not in images_bf:
                link_info['images'].append(image)
                images_bf.add(image_url)

    if soup and len(soup) > 0:
        for s in soup(['script', 'style']):
            s.decompose()

        link_info['corpus'] += " " + normalize_unicode_text(' '.join(soup.stripped_strings).lower())


def parse_website(url, link_info, internal_links, external_links, emails, phone_numbers, images_bf,
                  enable_javascript) -> set[str]:
    website_links = set()

    url = unquote(url)
    hostname = urlparse(url).hostname

    html, status_code = get_website_content(url, enable_javascript)

    if status_code >= 400 or html is None:
        return website_links

    html = clean_html(html)

    soup = BeautifulSoup(html, 'lxml')
    extracted_links = extract_website_links(hostname, soup, link_info)

    description, keywords, meta_title = filter_meta_data(soup)
    name, amp_title, images = filter_amp_data(soup, url)

    save_extracted_data(link_info, name, [meta_title, amp_title], keywords, description, images, soup, images_bf)

    for link in extracted_links:
        if 'mailto:' in link:
            email = link.split(':')[1]

            if validators.email(email) and email not in emails:
                emails.add(email)

            continue

        if 'tel:' in link:
            phone = link.split(':')[1]

            if phone not in phone_numbers:
                phone_numbers.add(phone)

            continue

        link = urljoin(url, link)

        link = remove_url_query(link)

        if not validators.url(link):
            continue
        if link in internal_links:
            continue

        if link_from_host(link, hostname):
            website_links.add(link)
            internal_links.add(link)
        else:
            if link not in external_links:
                external_links.add(link)

    return website_links


def aux_crawler(link, link_info, internal_links, external_links, emails, phone_numbers, images_bf, links_visited,
                enable_javascript):
    if links_visited[0] > MAX_CRAWL_DEPTH:
        return

    links_visited[0] += 1

    new_links = parse_website(link, link_info, internal_links, external_links, emails, phone_numbers, images_bf,
                              enable_javascript)

    for new_link in new_links:
        aux_crawler(new_link, link_info, internal_links, external_links, emails, phone_numbers, images_bf,
                    links_visited, enable_javascript)


def crawl_link(link) -> dict:
    link = standardize_url(link)
    link_info = {
        "original_link": link,
        "name": [],
        "title": [],
        "is_link_tree": False,
        "description": "",
        "keywords": [],
        "internal_links": [],
        "external_links": [],
        "emails": [],
        "phone_numbers": [],
        "images": [],
        "corpus": ""
    }

    internal_links = set()
    external_links = set()
    emails = set()
    phone_numbers = set()

    images_bf = BloomFilter()

    internal_links.add(link)

    aux_crawler(link, link_info, internal_links, external_links, emails, phone_numbers, images_bf, [0], False)

    images_bf.close()
    if len(internal_links) <= 1:
        images_bf = BloomFilter()
        aux_crawler(link, link_info, internal_links, external_links, emails, phone_numbers, images_bf, [0], True)

    link_info['internal_links'] = list(internal_links)
    link_info['external_links'] = list(external_links)
    link_info['emails'] = list(emails)
    link_info['phone_numbers'] = list(phone_numbers)

    return link_info


def crawl_links(links, links_per_user, entities_params, profile_names) -> tuple[list[dict], list[str]]:
    link_bf = BloomFilter()
    links_info = []

    link_queue = links.copy()

    for link in links:
        link_bf.add(link)

    link_counter = 0

    while len(link_queue) > 0 and link_counter < links_per_user:
        link = link_queue.pop()
        link_counter += 1

        link_info = crawl_link(link)

        link_score = calculate_link_profile_relatedness(link_info, profile_names)

        for internal_link in link_info.get('internal_links', []):
            if internal_link in link_queue:
                link_queue.remove(internal_link)

        if link_score < WEBSITE_RELATEDNESS_THRESHOLD:
            continue

        link_info['score'] = "{:.3f}".format(link_score)

        if link_info.get('is_link_tree', False):
            for external_link in link_info.get('external_links', []):
                if external_link not in link_bf:
                    link_queue.append(external_link)

        link_info['entities'] = extract_link_entities(link_info.get('corpus', ""), entities_params)

        link_info.pop('corpus')

        links_info.append(link_info)

    return links_info, link_queue
