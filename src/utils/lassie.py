import json
import locale

from requests.utils import default_user_agent
from urllib.parse import urljoin
from .filters import FILTER_MAPS
from .constants import CLEANER, FAKE_USER_AGENT

"""
    Functions taken from the lassie library: https://github.com/michaelhelmick/lassie
"""


def clean_text(value):
    """Removes all line breaks, new lines and tabs from the specified content
    :param value: Content to be cleansed
    :type value: string
    """
    return CLEANER.sub('', value)


def convert_to_int(value):
    """Attempts to convert a specified value to an integer
    :param value: Content to be converted into an integer
    :type value: string or int
    """
    if not value:
        return None

    # Apart from numbers also accept values that end with px
    if isinstance(value, str):
        value = value.strip(' px')

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_locale(value):
    value = value.replace('-', '_')
    the_locale = locale.normalize(value)

    if the_locale != value:
        # Should we return the actual locale, returned from the locale lib instead of splitting?
        try:
            return str(the_locale.split('.')[0])
        except IndexError:  # pragma: no cover
            pass
    return None


def normalize_image_data(data, url):
    # Create image list then remove duplicate images?
    img = {
        'src': urljoin(url, data.get('src')),
        'alt': data.get('alt', ''),
        'type': u'body_image',
    }

    # Only include width and height if included as an attribute of the element
    width = convert_to_int(data.get('width'))
    if width:
        img['width'] = width

    height = convert_to_int(data.get('height'))
    if height:
        img['height'] = height

    return img


def determine_user_agent(user_agent):
    if not user_agent or user_agent == default_user_agent():
        return FAKE_USER_AGENT

    return user_agent


def find_image_tag_data(source, soup, url):
    link = FILTER_MAPS['link'][source]

    html = soup.find_all('link', {link['key']: link['pattern']})

    images = []

    if link['type'] != 'url':
        for line in html:
            images.append({
                'src': urljoin(url, line.get('href')),
                'type': link['type'],
            })

    return images


def find_all_images(soup, url):
    all_images = soup.find_all('img')

    images = find_image_tag_data("canonical", soup, url)
    for image in all_images:
        item = normalize_image_data(image, url)

        images.append(item)

    return images


def filter_amp_data(soup, url):
    amp_scripts = soup.find_all('script', {'type': 'application/ld+json'})

    images = find_all_images(soup, url)
    name = ""
    title = ""

    if hasattr(soup.title, 'string'):
        title = soup.title.string

    for script in amp_scripts:
        content = script.contents
        _json = None
        try:
            _json = json.loads(content[0])
        except (IndexError, ValueError):
            continue

        if _json:
            if isinstance(_json, list):
                try:
                    # if the json is a list (see #46),
                    # set _json to the first item which _should_ be an object
                    _json = _json[0]
                except IndexError:  # pragma: no cover
                    pass

            if isinstance(_json, object):
                image = _json.get('image')
                if image:
                    if isinstance(image, str):
                        images.append({
                            'src': urljoin(url, image),
                        })
                    elif isinstance(image, list) or isinstance(image, object):
                        if isinstance(image, list):
                            image = image[0]

                        try:
                            image_list = image.get('@list')
                        except AttributeError:
                            image_list = [image]

                        if image_list:
                            for _image in image_list:
                                if isinstance(_image, str):
                                    images.append({
                                        'src': urljoin(url, _image),
                                    })
                                elif isinstance(_image, object):
                                    images.append({
                                        'src': urljoin(url, _image.get('url')),
                                        'width': convert_to_int(_image.get('width')),
                                        'height': convert_to_int(_image.get('height')),
                                    })
                        elif not image_list and image.get('url') and url != image.get('url'):
                            images.append({
                                'src': urljoin(url, image.get('url')),
                                'width': convert_to_int(image.get('width')),
                                'height': convert_to_int(image.get('height')),
                            })

                thumbnail_url = _json.get('thumbnailUrl')
                if thumbnail_url:
                    images.append({
                        'src': urljoin(url, thumbnail_url),
                    })

                name = _json.get("name")
                title += " " + _json.get('headline', '')

    return name, title, images


def filter_meta_data(soup, url=None, source="generic"):
    meta = FILTER_MAPS['meta'][source]
    meta_map = meta['map']

    html = soup.find_all('meta', {meta['key']: meta['pattern']})

    keywords = []
    description = ""
    title = ""

    for line in html:
        prop = line.get(meta['key'])
        value = line.get('content')
        _prop = meta_map.get(prop)

        if prop in meta_map and _prop:
            if prop == 'keywords':
                if isinstance(value, str):
                    keywords = [v.strip() for v in value.split(',')]
            elif prop == "description":
                description = value
            elif prop == "title":
                title = title
            else:
                print(f"{prop}: {value}")

    return description, keywords, title
