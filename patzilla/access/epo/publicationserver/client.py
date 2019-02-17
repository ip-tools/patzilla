# -*- coding: utf-8 -*-
# (c) 2015-2018 Andreas Motl <andreas.motl@ip-tools.org>
import logging
import requests
from patzilla.util.numbers.normalize import normalize_patent
from patzilla.util.network.browser import regular_user_agent
from pyramid.httpexceptions import HTTPNotFound


"""
Document retreiver for EPO publication server
https://data.epo.org/publication-server/
"""

logger = logging.getLogger(__name__)

def get_publication_server_pdf(document_number):

    patent = normalize_patent(document_number, as_dict=True, provider='espacenet')

    # Blueprint: https://data.epo.org/publication-server/pdf-document?cc=EP&pn=nnnnnn&ki=nn
    url_tpl = u'https://data.epo.org/publication-server/pdf-document?cc=EP&pn={number}&ki={kind}'

    url = url_tpl.format(**patent)

    logger.info('Accessing EPO publication server: {}'.format(url))
    response = requests.get(url, headers={'User-Agent': regular_user_agent})

    # Debugging
    #print 'response.content:\n', response.content

    if response.status_code == 200:
        payload = response.content
        return payload

    else:
        msg = 'No document found at EPO publication server for "{document_number}"'.format(**locals())
        logger.warn(msg)
        raise HTTPNotFound(msg)


if __name__ == '__main__':
    print get_publication_server_pdf('EP666666A2')
