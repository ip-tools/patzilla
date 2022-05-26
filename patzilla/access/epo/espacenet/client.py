# -*- coding: utf-8 -*-
# (c) 2015-2022 Andreas Motl <andreas.motl@ip-tools.org>
"""
Screenscraper for Espacenet
https://worldwide.espacenet.com/
"""
import logging

import requests
from BeautifulSoup import BeautifulSoup

from patzilla.util.network.browser import regular_user_agent
from patzilla.util.numbers.normalize import normalize_patent


logger = logging.getLogger(__name__)


def espacenet_fetch(document_number, section, element_id=None, element_class=None):

    patent = normalize_patent(document_number, as_dict=True, provider='espacenet')

    message_404 = 'No section "{section}" at Espacenet for "{document_number}"'.format(**locals())
    message_fail = 'Fetching section "{section}" from Espacenet for "{document_number}" failed'.format(**locals())

    # Examples:
    # - https://worldwide.espacenet.com/data/publicationDetails/biblio?CC=EP&NR=0666666A3&KC=A3&FT=D
    # - https://worldwide.espacenet.com/data/publicationDetails/claims?CC=EP&NR=0666666B1&KC=B1&FT=D
    url_tpl = u'https://worldwide.espacenet.com/data/publicationDetails/{section}?CC={country}&NR={number}'
    if 'kind' in patent and patent['kind']:
        patent["number"] += patent["kind"]
        url_tpl += '&KC={kind}'
    url_tpl += "&FT=D"

    url = url_tpl.format(section=section, **patent)

    logger.info('Accessing Espacenet: {}'.format(url))
    response = requests.get(url, headers={'User-Agent': regular_user_agent})

    # https://worldwide.espacenet.com/errorpages/error403.htm?reason=RobotAbuse&ip=89.247.174.135
    if "errorpages" in response.url:
        soup = BeautifulSoup(response.content)
        details = soup.find("h1").text
        details += ", see " + response.url
        message = "{}. Reason: {}".format(message_fail, details)
        raise ValueError(message)

    # Debugging
    #print 'response.content:\n', response.content

    if response.status_code == 200:
        # TODO: when no result, "Claims not available" appears in response body
        soup = BeautifulSoup(response.content)

        # Probe element by id.
        element = None
        if element_id is not None:
            element = soup.find('div', {'id': element_id})
            if element:
                element = element.find('p')
        elif element_class is not None:
            element = soup.find('p', {'class': element_class})
        else:
            details = "Either element_id or element_class must be used as selector"
            message = "{}. Reason: {}".format(message_fail, details)
            raise KeyError(message)

        if element:
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


def espacenet_abstract(document_number):
    """
    Return Espacenet abstract text
    https://worldwide.espacenet.com/data/publicationDetails/biblio?CC=US&NR=5770123A&DB=worldwide.espacenet.com&FT=D
    https://worldwide.espacenet.com/data/publicationDetails/biblio?CC=DE&NR=19814298A1&DB=worldwide.espacenet.com&FT=D
    """
    return espacenet_fetch(document_number, 'biblio', element_class='printAbstract')


def espacenet_description(document_number):
    """
    Return Espacenet description fulltext
    https://worldwide.espacenet.com/data/publicationDetails/description?CC=US&NR=5770123A&DB=worldwide.espacenet.com&FT=D
    https://worldwide.espacenet.com/data/publicationDetails/description?CC=DE&NR=19814298A1&DB=worldwide.espacenet.com&FT=D
    """
    return espacenet_fetch(document_number, 'description', 'description')


def espacenet_claims(document_number):
    """
    Return Espacenet claims fulltext
    https://worldwide.espacenet.com/data/publicationDetails/claims?CC=US&NR=5770123A&FT=D&DB=worldwide.espacenet.com
    https://worldwide.espacenet.com/data/publicationDetails/claims?CC=DE&NR=19814298A1&DB=worldwide.espacenet.com&FT=D
    """
    return espacenet_fetch(document_number, 'claims', 'claims')


if __name__ == '__main__':
    """
    python -m patzilla.access.epo.espacenet.client
    """
    numbers = [
        "US5770123A",
        "US6269530B1",
        "DE19814298A1",
        "DE29624638U1",
    ]
    for number in numbers:
        print("## {}".format(number))
        print("")
        print("### Claims")
        print(espacenet_claims(number))
        print("")
        print("### Description")
        print(espacenet_description(number))
        print("\n")
