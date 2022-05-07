import re
import chromedriver_autoinstaller

from selenium import webdriver
from selenium.webdriver.chromium.options import ChromiumOptions as Options

from .lassie import clean_text

chromedriver_autoinstaller.install()


def get_driver():
    options = Options()

    prefs = {
        "download_restrictions": 3,
    }

    options.headless = True
    options.add_argument("--enable-javascript")
    options.add_experimental_option("prefs", prefs)

    return webdriver.Chrome(options=options)


def clean_html(html):
    if '<html' not in html:
        html = re.sub(r'(?:<!DOCTYPE(?:\s\w)?>(?:<head>)?)',
                      '<!DOCTYPE html><html>', html)

    return clean_text(html)
