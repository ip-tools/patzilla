# -*- coding: utf-8 -*-
# (c) 2014-2016 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import re
import logging
import requests
from BeautifulSoup import BeautifulSoup
from patzilla.util.numbers.common import split_patent_number

log = logging.getLogger(__name__)

cipo_baseurl = 'http://brevets-patents.ic.gc.ca'

def fetch_first_drawing(patent):
    log.info('CIPO: Fetching first drawing of "{patent}"'.format(patent=patent))
    drawing_url = get_first_drawing_url(patent)
    if drawing_url:
        log.info('CIPO: Fetching first drawing from "{url}"'.format(url=drawing_url))
        response = requests.get(drawing_url)
        if response.status_code == 200:
            # v1: convert to tiff
            #return gif_to_tiff(response.content)

            # v2: let upstream infrastructure convert stuff universally
            return response.content
    else:
        log.warning("No content in main document page of '{}'".format(patent))


def fetch_document_index(patent):
    # http://brevets-patents.ic.gc.ca/opic-cipo/cpd/eng/patent/141597/summary.html#cn-cont
    url_tpl = cipo_baseurl + '/opic-cipo/cpd/eng/patent/{number}/summary.html'
    url = url_tpl.format(number=patent['number'])
    log.info('CIPO: Index url is "{}"'.format(url))
    response = requests.get(url)
    if response.status_code == 200:
        return response.text

def fetch_images_index(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text

def get_first_drawing_url(patent):

    # A. Industrial designs
    # http://www.ic.gc.ca/cgi-bin/sc_mrksv/cipo/ind-design/getImage.pl?appNum=140249&extension=0&imageType=1&order=1&rotation=0&imageBrand=Application
    if patent['kind'] == 'S':
        url_tpl = 'http://www.ic.gc.ca/cgi-bin/sc_mrksv/cipo/ind-design/getImage.pl?appNum={number}&extension=0&imageType=1&order=1&rotation=0&imageBrand=Application'
        url = url_tpl.format(number=patent['number'])
        return url

    # B. Patents

    # 1. fetch and parse document index page
    document_index_html = fetch_document_index(patent)
    soup = BeautifulSoup(document_index_html)
    anchors = soup.findAll('a')

    images_index_url = None
    for anchor in anchors:
        if "Drawings" in str(anchor):
            images_index_url = cipo_baseurl + anchor['href']
            break

    if not images_index_url:
        return


    # 2. fetch and parse images index page
    images_index_html = fetch_images_index(images_index_url)
    soup = BeautifulSoup(images_index_html)
    # <img src="/opic-cipo/cpd/page/141597_20130713_drawings_page1_scale25_rotate0.gif?page=3&amp;section=drawings&amp;scale=25&amp;rotation=0&amp;type=" alt="Canadian Patent Document 141597. Drawings page. Image 1 of 3" />
    first_drawing_url = cipo_baseurl + soup.find('img', src=re.compile(ur'/opic-cipo/cpd/page'))['src']

    return first_drawing_url

if __name__ == '__main__':

    numbers = [
        'CA141597A'
    ]
    for number in numbers:
        payload = fetch_first_drawing(split_patent_number(number))
        if payload:
            #print "payload length:", len(payload)
            print payload
        else:
            print "not found"
