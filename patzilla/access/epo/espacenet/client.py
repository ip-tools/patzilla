# -*- coding: utf-8 -*-
# (c) 2015-2018 Andreas Motl <andreas.motl@ip-tools.org>
import logging
import requests
from BeautifulSoup import BeautifulSoup
from patzilla.util.network.browser import regular_user_agent
from patzilla.util.numbers.normalize import normalize_patent


"""
Screenscraper for Espacenet
http://worldwide.espacenet.com/
"""

logger = logging.getLogger(__name__)

def espacenet_fetch(document_number, section, element_id):

    patent = normalize_patent(document_number, as_dict=True, provider='espacenet')

    # Blueprint: https://worldwide.espacenet.com/publicationDetails/biblio?CC=EP&NR=0666666&KC=A3
    url_tpl = u'https://worldwide.espacenet.com/data/publicationDetails/{section}?CC={country}&NR={number}'
    if 'kind' in patent and patent['kind']:
        url_tpl += '&KC={kind}'

    url = url_tpl.format(section=section, **patent)

    logger.info('Accessing Espacenet: {}'.format(url))
    response = requests.get(url, headers={'User-Agent': regular_user_agent})

    # Debugging
    #print 'response.content:\n', response.content

    message_404 = 'No section "{section}" at Espacenet for "{document_number}"'.format(**locals())
    message_fail = 'Fetching section "{section}" from Espacenet for "{document_number}" failed'.format(**locals())

    if response.status_code == 200:
        # TODO: when no result, "Claims not available" appears in response body
        soup = BeautifulSoup(response.content)
        element = soup.find('div', {'id': element_id})
        if element:
            element = element.find('p')
            lang = element['lang']
            del element['class']
            content = element.prettify()
        else:
            raise KeyError(message_404)

        data = {
            'xml': content,
            'lang': lang,
            'source': 'espacenet',
            }

        return data

    elif response.status_code == 404:
        raise KeyError(message_404)

    else:

        if 'Entity not found' in response.content:
            raise KeyError(message_404)
        else:
            raise ValueError(message_fail)


def espacenet_description(document_number):
    """
    Return Espacenet description fulltext
    http://worldwide.espacenet.com/publicationDetails/description?CC=US&NR=5770123A&DB=worldwide.espacenet.com&FT=D
    http://worldwide.espacenet.com/publicationDetails/description?CC=DE&NR=19814298A1&DB=worldwide.espacenet.com&FT=D
    """
    return espacenet_fetch(document_number, 'description', 'description')


def espacenet_claims(document_number):
    """
    Return Espacenet claims fulltext
    http://worldwide.espacenet.com/publicationDetails/claims?CC=US&NR=5770123A&FT=D&DB=worldwide.espacenet.com
    http://worldwide.espacenet.com/publicationDetails/claims?CC=DE&NR=19814298A1&DB=worldwide.espacenet.com&FT=D
    """
    return espacenet_fetch(document_number, 'claims', 'claims')


if __name__ == '__main__':
    #print espacenet_description('DE19814298A1')
    #print espacenet_description('US5770123A')

    #print espacenet_claims('DE19814298A1')
    print espacenet_claims('US5770123A')
