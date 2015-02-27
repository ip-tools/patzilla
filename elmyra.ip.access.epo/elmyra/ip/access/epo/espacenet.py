# -*- coding: utf-8 -*-
# (c) 2015 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import requests
from BeautifulSoup import BeautifulSoup
from elmyra.ip.util.numbers.normalize import normalize_patent


"""
Screenscraper for Espacenet
http://worldwide.espacenet.com/
"""

def espacenet_description(document_number):
    """
    Return Espacenet description fulltext
    http://worldwide.espacenet.com/publicationDetails/description?CC=US&NR=5770123A&DB=worldwide.espacenet.com&FT=D
    http://worldwide.espacenet.com/publicationDetails/description?CC=DE&NR=19814298A1&DB=worldwide.espacenet.com&FT=D
    """

    patent = normalize_patent(document_number, as_dict=True)
    url_tpl = u'http://worldwide.espacenet.com/publicationDetails/description?CC={country}&NR={number}{kind}&DB=worldwide.espacenet.com&FT=D'
    url = url_tpl.format(**patent)

    response = requests.get(url)
    soup = BeautifulSoup(response.content)
    description = soup.find('div', {'id': 'description'}).find('p')
    lang = description['lang']
    del description['class']
    content = description.prettify()

    data = {
        'xml': content,
        'lang': lang,
        'source': 'espacenet',
    }

    return data

def espacenet_claims(document_number):
    """
    Return Espacenet claims fulltext
    http://worldwide.espacenet.com/publicationDetails/claims?CC=US&NR=5770123A&FT=D&DB=worldwide.espacenet.com
    http://worldwide.espacenet.com/publicationDetails/claims?CC=DE&NR=19814298A1&DB=worldwide.espacenet.com&FT=D
    """

    patent = normalize_patent(document_number, as_dict=True)
    url_tpl = u'http://worldwide.espacenet.com/publicationDetails/claims?CC={country}&NR={number}{kind}&DB=worldwide.espacenet.com&FT=D'
    url = url_tpl.format(**patent)

    response = requests.get(url)
    soup = BeautifulSoup(response.content)
    description = soup.find('div', {'id': 'claims'}).find('p')
    lang = description['lang']
    del description['class']
    content = description.prettify()

    data = {
        'xml': content,
        'lang': lang,
        'source': 'espacenet',
    }

    return data


if __name__ == '__main__':
    #print espacenet_description('DE19814298A1')
    #print espacenet_description('US5770123A')

    #print espacenet_claims('DE19814298A1')
    print espacenet_claims('US5770123A')
