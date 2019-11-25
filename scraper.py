import requests
from bs4 import BeautifulSoup
import argparse
import re
from pprint import pprint
import os
import json


# URL = "https://poshmark.ca/listing/Aritzia-Wilfred-Free-Zlata-Sweater-Cardigan-M-Grey-5dba2316c953d8f4358c5ce1"
# URL = "https://poshmark.ca/listing/Free-People-Lavender-Embroidered-Mini-5dd090d5aa7ed3a65c0ea6b2"


def get_soup(url):
    """ Get Soup Object from request content
        """
    res = requests.get(url=url)
    soup = BeautifulSoup(res.text, "html.parser")
    infor_form = soup.find("div", {"id": "content"})
    return infor_form


def get_value(soup, tag, cond, default=None):
    """ Get value of element from soup by condition
        """
    ele = soup.find(tag, cond)
    if ele:
        return ele.text.strip()
    return default


def scrap_unit(soup):
    """
        Extract necessary data from soup
        """

    # Title
    title = get_value(soup, 'h1', {'class', 'title'}, '')

    # New With Tags
    cond_tag = get_value(soup, 'p', {'class': 'condition-tags'}, 'NO')
    if cond_tag:
        title = title.replace(cond_tag, '').strip()
        cond_tag = 'YES'

    # Brand
    brand = get_value(soup, 'a', {'class', 'brand'})

    # Description
    description = get_value(soup, 'div', {'class', 'description'})

    # Size
    size = get_value(soup, 'label', {'class', 'size-box'})

    # Prices
    listing_price = get_value(soup, 'div', {'class', 'price'})
    ori_price = get_value(soup, 'span', {'class', 'original'})
    if listing_price and ori_price:
        ori_price = re.findall("[-+]?\d*\.\d+|\d+", ori_price)[0]
        listing_price = re.findall("[-+]?\d*\.\d+|\d+", listing_price.replace(ori_price, '').strip())[0]

    # Images
    image_div = soup.find(id='imageCarousel')
    images = []
    if image_div:
        image_tags = image_div.find_all('img', {'class', 'add_pin_it_btn'})
        for tag in image_tags:
            title = tag['title']
            src = tag['src']
            alt = tag['alt']
            images.append({'src': src, 'title': title, 'alt': alt})

    result = {
        'Title': title,
        'Description': description,
        'Photo': images,
        'Brand': brand,
        'Size': size,
        "Custom Size": "",
        'Listing Price': listing_price,
        'Original Price': ori_price,
        'New With Tags': cond_tag
    }

    # tag-lists
    tag_lists = soup.find_all('div', {'class': 'tag-list'})
    categories = []
    colors = []

    if len(tag_lists) > 0:
        # get category tags
        tags = tag_lists[0].find_all('a', {'class': 'tag'})
        for ind, tag in enumerate(tags):
            result.update({'Category%s' % (ind + 1): tag.text})

    if len(tag_lists) > 1:
        # get colors
        tags = tag_lists[1].find_all('a', {'class': 'tag'})
        for ind, tag in enumerate(tags):
            result.update({'Color%s' % (ind + 1): tag.text})

    pprint(result)
    store_result(result)


def store_result(arr):
    """
        Store result to json file and download images
        """
    title = arr['Title'].replace('/', '-')
    # create directory
    if not os.path.exists(title):
        os.makedirs(title)

    with open('%s/%s.json' % (title, title), 'w') as f:
        f.write(json.dumps(arr))
    f.close()

    # images download
    images = arr['Photo']
    for image in images:
        filename = image['src'].split('/')[-1]
        file_path = os.path.join(title, filename)
        r = requests.get(image['src'], allow_redirects=True)
        open(file_path, 'wb').write(r.content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', help='url', required=True)
    args = parser.parse_args()
    url = args.url
    print("URL is", url)
    print("Scraping now ...")

    soup = get_soup(url)
    scrap_unit(soup)
    print("END!")
